"""V2Node 服务端 API 业务逻辑。"""

import base64
import hashlib
import time
from typing import Any

import orjson
from app.core.cache import RuntimeCache
from app.core.queue import PostgresQueue

from app.models.server_route.entity import ServerRoute
from app.models.server_v2node.entity import ServerV2Node
from app.models.user.entity import User
from app.queues.names import QUEUE_STAT, QUEUE_TRAFFIC_FETCH
from app.repositories.server_route import ServerRouteRepository
from app.repositories.server_v2node import ServerV2NodeRepository
from app.services.setting import SettingService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


class ServerService:
    """只复刻原版 V2\\Server\\ServerController 的配置拉取逻辑。"""

    def __init__(
        self,
        node_repo: ServerV2NodeRepository,
        route_repo: ServerRouteRepository,
        setting_service: SettingService,
        user_repo: Any,
        cache: RuntimeCache,
        db: AsyncSession,
    ):
        self.node_repo = node_repo
        self.route_repo = route_repo
        self.setting_service = setting_service
        self.user_repo = user_repo
        self.cache = cache
        self.db = db

    async def get_v2node_config(self, node_id: int) -> dict[str, Any] | None:
        """构造 /api/v2/server/config 响应体。"""
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            return None

        response: dict[str, Any] = {
            "listen_ip": node.listen_ip,
            "server_port": node.server_port,
            "network": node.network,
            "network_settings": _json_cast(node.network_settings),
            "protocol": node.protocol,
            "tls": node.tls,
            "tls_settings": _json_cast(node.tls_settings),
            "encryption": node.encryption,
            "encryption_settings": _json_cast(node.encryption_settings),
            "flow": node.flow,
            "cipher": node.cipher,
            "congestion_control": node.congestion_control,
            "zero_rtt_handshake": bool(node.zero_rtt_handshake),
            "up_mbps": node.up_mbps,
            "down_mbps": node.down_mbps,
            "obfs": node.obfs,
            "obfs_password": node.obfs_password,
            "padding_scheme": _json_cast(node.padding_scheme),
        }

        if node.cipher == "2022-blake3-aes-128-gcm":
            response["server_key"] = _get_server_key(node.created_at, 16)
        if node.cipher == "2022-blake3-aes-256-gcm":
            response["server_key"] = _get_server_key(node.created_at, 32)

        response["ignore_client_bandwidth"] = node.up_mbps == 0 and node.down_mbps == 0
        response["base_config"] = {
            "push_interval": await self.setting_service.get_int("server_push_interval", 60),
            "pull_interval": await self.setting_service.get_int("server_pull_interval", 60),
            "node_report_min_traffic": await self.setting_service.get_int("server_node_report_min_traffic", 0),
            "device_online_min_traffic": await self.setting_service.get_int("server_device_online_min_traffic", 0),
        }

        route_ids = _int_list_cast(node.route_id)
        if route_ids:
            response["routes"] = [_route_to_config(route) for route in await self.route_repo.get_by_ids_ordered(route_ids)]

        return response

    async def get_uniproxy_node(self, node_id: int, node_type: str) -> ServerV2Node | None:
        """按当前项目统一 v2node 表查找 UniProxy 节点。"""
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            return None
        if node_type != "v2node" and _normalize_node_type(node.protocol) != node_type:
            return None
        return node

    async def mark_uniproxy_check(self, node_type: str, node_id: int) -> None:
        await self.cache.set(_server_cache_key(node_type, "LAST_CHECK_AT", node_id), int(time.time()), ex=3600)

    async def get_available_users(self, group_id: Any) -> list[dict[str, Any]]:
        """复刻 ServerService::getAvailableUsers。"""
        group_ids = _int_list_cast(group_id)
        if not group_ids:
            return []

        now = int(time.time())
        stmt = (
            select(User)
            .where(User.group_id.in_(group_ids))  # type: ignore[attr-defined]
            .where((User.u + User.d) < User.transfer_enable)  # type: ignore[operator]
            .where((User.expired_at >= now) | (User.expired_at.is_(None)))  # type: ignore[attr-defined]
            .where(User.banned.is_(False))  # type: ignore[attr-defined]
        )
        result = await self.db.execute(stmt)
        return [_user_to_node_dict(user) for user in result.scalars().all()]

    async def handle_uniproxy_push(
        self,
        node: ServerV2Node,
        node_type: str,
        data: dict[str, Any],
        queue: PostgresQueue,
    ) -> None:
        """处理 UniProxy 流量上报。"""
        node_id = int(node.id or 0)
        await self.cache.set(_server_cache_key(node_type, "ONLINE_USER", node_id), len(data), ex=3600)
        await self.cache.set(_server_cache_key(node_type, "LAST_PUSH_AT", node_id), int(time.time()), ex=3600)

        if not data:
            return

        server = {"id": node_id, "rate": node.rate}
        await queue.enqueue_job("traffic_fetch", data, server, node_type, _queue_name=QUEUE_TRAFFIC_FETCH)
        await queue.enqueue_job("stat_user", data, server, node_type, "d", _queue_name=QUEUE_STAT)
        await queue.enqueue_job("stat_server", data, server, node_type, "d", _queue_name=QUEUE_STAT)

    async def get_alive_list(self) -> dict[str, int]:
        """复刻 UniProxyController::alivelist。"""
        cached = await _cache_get_json(self.cache, "ALIVE_LIST")
        if isinstance(cached, dict):
            return {str(key): int(value) for key, value in cached.items()}

        user_ids = await self._get_device_limited_user_ids()
        if not user_ids:
            await self.cache.set("ALIVE_LIST", {}, ex=60)
            return {}

        keys = [f"ALIVE_IP_USER_{user_id}" for user_id in user_ids]
        values = await self.cache.mget(keys)
        alive: dict[str, int] = {}
        for user_id, raw in zip(user_ids, values, strict=False):
            data = _loads_cache_json(raw)
            if isinstance(data, dict) and "alive_ip" in data:
                alive[str(user_id)] = int(data["alive_ip"])
        await self.cache.set("ALIVE_LIST", alive, ex=60)
        return alive

    async def handle_alive(self, node_type: str, node_id: int, data: dict[str, Any]) -> None:
        """复刻 UniProxyController::alive。"""
        update_at = int(time.time())
        user_ids = [str(uid) for uid in data.keys()]
        keys = [f"ALIVE_IP_USER_{uid}" for uid in user_ids]
        cached_values = await self.cache.mget(keys) if keys else []
        cached = {
            key: _loads_cache_json(value)
            for key, value in zip(keys, cached_values, strict=False)
        }
        device_limit_mode = await self.setting_service.get_int("device_limit_mode", 0)

        for uid, ips in data.items():
            if not str(uid).isnumeric() or not isinstance(ips, list):
                continue
            key = f"ALIVE_IP_USER_{uid}"
            ips_array = cached.get(key)
            if not isinstance(ips_array, dict):
                ips_array = {}

            ips_array[f"{node_type}{node_id}"] = {"aliveips": ips, "lastupdateAt": update_at}
            for node_key, old_ips in list(ips_array.items()):
                if node_key == "alive_ip" or not isinstance(old_ips, dict):
                    continue
                if update_at - int(old_ips.get("lastupdateAt") or 0) > 100:
                    ips_array.pop(node_key, None)

            ips_array["alive_ip"] = _count_alive_ips(ips_array, unique_ip=device_limit_mode == 1)
            await self.cache.set(key, ips_array, ex=120)

        await self.cache.delete("ALIVE_LIST")

    async def _get_device_limited_user_ids(self) -> list[int]:
        now = int(time.time())
        stmt = (
            select(User.id)
            .where((User.u + User.d) < User.transfer_enable)  # type: ignore[operator]
            .where((User.expired_at >= now) | (User.expired_at.is_(None)))  # type: ignore[attr-defined]
            .where(User.banned.is_(False))  # type: ignore[attr-defined]
            .where(User.device_limit > 0)  # type: ignore[operator]
        )
        result = await self.db.execute(stmt)
        return [int(user_id) for user_id in result.scalars().all() if user_id is not None]


def _user_to_node_dict(user: User) -> dict[str, Any]:
    """节点端用户视图。

    对齐原版节点端需要的用户属性，同时避免下发 password/token/email 等敏感认证字段。
    """
    return _compact_none(
        {
            "id": user.id,
            "uuid": user.uuid,
            "speed_limit": user.speed_limit,
            "device_limit": user.device_limit,
            "u": user.u,
            "d": user.d,
            "transfer_enable": user.transfer_enable,
            "expired_at": user.expired_at,
            "t": user.t,
            "group_id": user.group_id,
            "plan_id": user.plan_id,
        }
    )


def _json_cast(value: Any) -> Any:
    """模拟 Laravel array cast：JSON 字符串转数组/对象，空值保持 None。"""
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    try:
        return orjson.loads(value)
    except orjson.JSONDecodeError:
        return value


def _int_list_cast(value: Any) -> list[int]:
    parsed = _json_cast(value)
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


def _route_to_config(route: ServerRoute) -> dict[str, Any]:
    match = _route_match_cast(route.match)
    return {
        "id": route.id,
        "match": match,
        "action": route.action,
        "action_value": route.action_value,
    }


def _route_match_cast(value: Any) -> Any:
    parsed = _json_cast(value)
    return parsed if isinstance(parsed, (dict, list)) else value


def _get_server_key(timestamp: int, length: int) -> str:
    digest = hashlib.md5(str(timestamp).encode()).hexdigest()[:length]
    return base64.b64encode(digest.encode()).decode()


def _normalize_node_type(node_type: Any) -> str:
    value = str(node_type or "")
    if value == "v2ray":
        return "vmess"
    if value == "hysteria2":
        return "hysteria"
    return value


def _server_cache_key(node_type: str, name: str, node_id: int) -> str:
    return f"SERVER_{node_type.upper()}_{name}_{node_id}"


def _compact_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


async def _cache_get_json(cache: RuntimeCache, key: str) -> Any:
    return _loads_cache_json(await cache.get(key))


def _loads_cache_json(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return orjson.loads(raw)
    except (orjson.JSONDecodeError, TypeError):
        return None


def _count_alive_ips(ips_array: dict[str, Any], unique_ip: bool) -> int:
    if unique_ip:
        ip_map: set[str] = set()
        for node_data in ips_array.values():
            if not isinstance(node_data, dict) or "aliveips" not in node_data:
                continue
            for ip_node_id in node_data["aliveips"]:
                ip_map.add(str(ip_node_id).split("_", 1)[0])
        return len(ip_map)

    count = 0
    for node_data in ips_array.values():
        if isinstance(node_data, dict) and isinstance(node_data.get("aliveips"), list):
            count += len(node_data["aliveips"])
    return count
