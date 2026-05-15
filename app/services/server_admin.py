"""管理端节点、分组和路由规则服务。"""

import hashlib
import secrets
from typing import Any

import orjson
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.plan.entity import Plan
from app.models.server_group.dto import ServerGroupCreate, ServerGroupUpdate
from app.models.server_group.entity import ServerGroup
from app.models.server_route.dto import ServerRouteCreate, ServerRouteUpdate
from app.models.server_route.entity import ServerRoute
from app.models.server_v2node.dto import ServerV2NodeCreate, ServerV2NodeUpdate
from app.models.server_v2node.entity import ServerV2Node
from app.models.user.entity import User
from app.repositories.server_group import ServerGroupRepository
from app.repositories.server_route import ServerRouteRepository
from app.repositories.server_v2node import ServerV2NodeRepository

ROUTE_ACTIONS = {"block", "block_ip", "block_port", "protocol", "dns", "route", "route_ip", "default_out"}
PROTOCOLS = {"shadowsocks", "vmess", "vless", "trojan", "tuic", "hysteria2", "hysteria", "anytls"}
NETWORKS = {"tcp", "ws", "grpc", "http", "httpupgrade", "xhttp"}


class ServerAdminService:
    """管理端节点模块。"""

    def __init__(
        self,
        db: AsyncSession,
        group_repo: ServerGroupRepository,
        route_repo: ServerRouteRepository,
        node_repo: ServerV2NodeRepository,
    ):
        self.db = db
        self.group_repo = group_repo
        self.route_repo = route_repo
        self.node_repo = node_repo

    async def list_groups(self) -> list[dict[str, Any]]:
        groups = await self.group_repo.list_all()
        result: list[dict[str, Any]] = []
        for group in groups:
            result.append(
                {
                    **_model_dict(group),
                    "user_count": await self._count_users_in_group(int(group.id or 0)),
                    "server_count": await self._count_nodes_in_group(int(group.id or 0)),
                }
            )
        return result

    async def create_group(self, data: ServerGroupCreate) -> ServerGroup:
        if not data.name:
            raise BadRequestException("组名不能为空")
        return await self.group_repo.create(ServerGroup(name=data.name))

    async def update_group(self, group_id: int, data: ServerGroupUpdate) -> ServerGroup:
        group = await self.group_repo.get_by_id(group_id)
        if group is None:
            raise NotFoundException("组不存在")
        if data.name is not None:
            if not data.name:
                raise BadRequestException("组名不能为空")
            group.name = data.name
        return await self.group_repo.update(group)

    async def delete_group(self, group_id: int) -> None:
        group = await self.group_repo.get_by_id(group_id)
        if group is None:
            raise NotFoundException("组不存在")
        if await self._count_nodes_in_group(group_id):
            raise ConflictException("该组已被节点所使用，无法删除")
        if await self._count_plans_in_group(group_id):
            raise ConflictException("该组已被订阅所使用，无法删除")
        if await self._count_users_in_group(group_id):
            raise ConflictException("该组已被用户所使用，无法删除")
        await self.group_repo.delete(group)

    async def list_routes(self) -> list[dict[str, Any]]:
        routes = await self.route_repo.list_all()
        return [_route_dict(route) for route in routes]

    async def create_route(self, data: ServerRouteCreate) -> ServerRoute:
        payload = _normalize_route(data.model_dump())
        return await self.route_repo.create(ServerRoute(**payload))

    async def update_route(self, route_id: int, data: ServerRouteUpdate) -> ServerRoute:
        route = await self.route_repo.get_by_id(route_id)
        if route is None:
            raise NotFoundException("路由不存在")
        payload = _normalize_route(data.model_dump(exclude_unset=True), partial=True)
        for key, value in payload.items():
            setattr(route, key, value)
        return await self.route_repo.update(route)

    async def delete_route(self, route_id: int) -> None:
        route = await self.route_repo.get_by_id(route_id)
        if route is None:
            raise NotFoundException("路由不存在")
        if await self._count_nodes_in_route(route_id):
            raise ConflictException("该路由已被节点所使用，无法删除")
        await self.route_repo.delete(route)

    async def list_nodes(self) -> list[dict[str, Any]]:
        return [_node_dict(node) for node in await self.node_repo.list_all()]

    async def get_node(self, node_id: int) -> dict[str, Any]:
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            raise NotFoundException("节点不存在")
        return _node_dict(node)

    async def create_node(self, data: ServerV2NodeCreate) -> dict[str, Any]:
        payload = _normalize_node(data.model_dump())
        node = await self.node_repo.create(ServerV2Node(**payload))
        return _node_dict(node)

    async def update_node(self, node_id: int, data: ServerV2NodeUpdate) -> dict[str, Any]:
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            raise NotFoundException("节点不存在")
        payload = _normalize_node(data.model_dump(exclude_unset=True), partial=True)
        for key, value in payload.items():
            setattr(node, key, value)
        node = await self.node_repo.update(node)
        return _node_dict(node)

    async def delete_node(self, node_id: int) -> None:
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            raise NotFoundException("节点不存在")
        await self.node_repo.delete(node)

    async def copy_node(self, node_id: int) -> dict[str, Any]:
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            raise NotFoundException("节点不存在")
        payload = _model_dict(node)
        payload.pop("id", None)
        payload.pop("created_at", None)
        payload.pop("updated_at", None)
        payload["show"] = False
        copy = await self.node_repo.create(ServerV2Node(**payload))
        return _node_dict(copy)

    async def sort_nodes(self, sorts: dict[int | str, int]) -> bool:
        for raw_id, sort in sorts.items():
            node = await self.node_repo.get_by_id(int(raw_id))
            if node is None:
                continue
            node.sort = int(sort)
            await self.node_repo.update(node)
        return True

    async def _count_users_in_group(self, group_id: int) -> int:
        result = await self.db.execute(select(func.count()).select_from(User).where(User.group_id == group_id))
        return int(result.scalar_one())

    async def _count_plans_in_group(self, group_id: int) -> int:
        result = await self.db.execute(select(func.count()).select_from(Plan).where(Plan.group_id == group_id))
        return int(result.scalar_one())

    async def _count_nodes_in_group(self, group_id: int) -> int:
        count = 0
        for node in await self.node_repo.list_all():
            if group_id in _int_list_cast(node.group_id):
                count += 1
        return count

    async def _count_nodes_in_route(self, route_id: int) -> int:
        count = 0
        for node in await self.node_repo.list_all():
            if route_id in _int_list_cast(node.route_id):
                count += 1
        return count


def _normalize_route(data: dict[str, Any], partial: bool = False) -> dict[str, Any]:
    action = data.get("action")
    if action is not None and action not in ROUTE_ACTIONS:
        raise BadRequestException("动作类型参数有误")
    if not partial and not data.get("remarks"):
        raise BadRequestException("备注不能为空")
    if action == "default_out":
        data["match"] = []
    elif "match" in data:
        match = data.get("match")
        if not match and not partial:
            raise BadRequestException("匹配值不能为空")
        data["match"] = _json_dump([item for item in match if item] if isinstance(match, list) else match)
    return data


def _normalize_node(data: dict[str, Any], partial: bool = False) -> dict[str, Any]:
    protocol = data.get("protocol")
    network = data.get("network")
    if protocol is not None and protocol not in PROTOCOLS:
        raise BadRequestException("协议类型参数有误")
    if network is not None and network not in NETWORKS:
        raise BadRequestException("传输类型参数有误")
    if not partial:
        for field in ("group_id", "name", "host", "port", "server_port", "protocol", "tls", "network", "rate"):
            if data.get(field) in (None, ""):
                raise BadRequestException(f"{field} 不能为空")

    protocol = data.get("protocol")
    if protocol == "anytls" and data.get("tls") == 0:
        data["tls"] = 1
    if protocol in {"hysteria2", "hysteria", "trojan", "tuic"}:
        data["tls"] = 1
    if protocol == "shadowsocks" and not data.get("cipher"):
        data["cipher"] = "aes-128-gcm"

    for field in ("group_id", "route_id", "tags", "padding_scheme"):
        if field in data:
            data[field] = _json_dump(data[field])

    for field in ("tls_settings", "network_settings", "encryption_settings"):
        if field in data:
            data[field] = _json_object_dump(data[field], field)

    if data.get("tls") == 2:
        settings = _json_load(data.get("tls_settings")) or {}
        settings.setdefault("public_key", secrets.token_urlsafe(32))
        settings.setdefault("private_key", secrets.token_urlsafe(32))
        settings.setdefault("short_id", hashlib.sha1(settings["private_key"].encode()).hexdigest()[:8])
        settings.setdefault("server_port", "443")
        data["tls_settings"] = _json_dump(settings)

    if data.get("network") not in (None, "tcp") and data.get("encryption") != "mlkem768x25519plus":
        data["flow"] = None

    if data.get("obfs") and not data.get("obfs_password"):
        data["obfs_password"] = secrets.token_urlsafe(12)
    if "obfs" in data and not data.get("obfs"):
        data["obfs_password"] = None

    data.setdefault("up_mbps", 0)
    data.setdefault("down_mbps", 0)
    return data


def _json_dump(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        try:
            return orjson.loads(value)
        except orjson.JSONDecodeError:
            return value
    return value


def _json_object_dump(value: Any, field: str) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            parsed = orjson.loads(value)
        except orjson.JSONDecodeError as exc:
            raise BadRequestException(f"{field} 必须是 JSON 对象") from exc
        if not isinstance(parsed, dict):
            raise BadRequestException(f"{field} 必须是 JSON 对象")
        return parsed
    if not isinstance(value, dict):
        raise BadRequestException(f"{field} 必须是 JSON 对象")
    return value


def _json_load(value: Any) -> Any:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        return value
    try:
        return orjson.loads(value)
    except orjson.JSONDecodeError:
        return value


def _route_dict(route: ServerRoute) -> dict[str, Any]:
    data = _model_dict(route)
    parsed = _json_load(route.match)
    if isinstance(parsed, list):
        data["match"] = parsed
    return data


def _node_dict(node: ServerV2Node) -> dict[str, Any]:
    data = _model_dict(node)
    data["type"] = "v2node"
    for field in ("group_id", "route_id", "tags", "tls_settings", "network_settings", "encryption_settings", "padding_scheme"):
        data[field] = _json_load(data.get(field))
    return data


def _model_dict(model: Any) -> dict[str, Any]:
    return model.model_dump()


def _int_list_cast(value: Any) -> list[int]:
    parsed = _json_load(value)
    if parsed in (None, ""):
        return []
    if isinstance(parsed, int):
        return [parsed]
    if isinstance(parsed, str):
        return [int(item.strip()) for item in parsed.split(",") if item.strip().isdigit()]
    if isinstance(parsed, list):
        result: list[int] = []
        for item in parsed:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return result
    return []
