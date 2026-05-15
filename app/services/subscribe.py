"""订阅服务，业务层只负责取数、归一化和调度模板。"""

import base64
import hashlib
import hmac
import ipaddress
import secrets
import time
import urllib.parse
from pathlib import Path
from typing import Any

import orjson
from jinja2 import Environment, FileSystemLoader

from app.core.cache import RuntimeCache
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.models.plan.entity import Plan
from app.models.server_v2node.entity import ServerV2Node
from app.models.user.entity import User
from app.repositories.plan import PlanRepository
from app.repositories.server_v2node import ServerV2NodeRepository
from app.repositories.user import UserRepository
from app.services.setting import SettingService

_template_dir = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_template_dir),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.do"],
)

_env.filters["to_json"] = lambda value: orjson.dumps(value).decode()
_env.filters["to_pretty_json"] = lambda value: orjson.dumps(value, option=orjson.OPT_INDENT_2).decode()
_env.filters["b64"] = lambda value: base64.b64encode(str(value).encode()).decode()
_env.filters["b64_json"] = lambda value: base64.b64encode(orjson.dumps(value)).decode()
_env.filters["b64_urlsafe"] = lambda value: _base64_urlsafe(str(value).encode())
_env.filters["query"] = lambda value: urllib.parse.urlencode(
    {key: val for key, val in dict(value).items() if val not in (None, "")}
)
_env.filters["urlencode"] = lambda value: urllib.parse.quote(str(value))
_env.filters["boolstr"] = lambda value: "true" if bool(value) else "false"

_CLASH_FORMATS = {"clash", "clash_meta", "clash_verge", "clash_nyanpasu", "stash"}
_GENERAL_FORMATS = {"general", "passwall", "ssrplus", "v2rayn", "v2rayng"}
_BASE64_FORMATS = _GENERAL_FORMATS | {"v2raytun", "sagernet", "shadowrocket", "quantumultx"}
_SS_SIP008_CIPHERS = {"aes-128-gcm", "aes-192-gcm", "aes-256-gcm", "chacha20-ietf-poly1305"}


class SubscribeService:
    """用户订阅、订阅 token 和可用节点。"""

    def __init__(
        self,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
        node_repo: ServerV2NodeRepository,
        setting_service: SettingService,
        cache: RuntimeCache,
    ):
        self.user_repo = user_repo
        self.plan_repo = plan_repo
        self.node_repo = node_repo
        self.setting_service = setting_service
        self.cache = cache

    async def get_user_subscribe_info(self, user_id: int) -> dict[str, Any]:
        """获取用户订阅面板信息。"""
        user = await self._get_user(user_id)
        plan = await self.plan_repo.get_by_id(user.plan_id) if user.plan_id else None
        alive_data = await _cache_get_json(self.cache, f"ALIVE_IP_USER_{user_id}")
        alive_ip = int(alive_data.get("alive_ip", 0)) if isinstance(alive_data, dict) else 0
        return {
            "plan_id": user.plan_id,
            "plan": _plan_to_dict(plan) if plan else None,
            "token": user.token,
            "expired_at": user.expired_at,
            "u": user.u,
            "d": user.d,
            "transfer_enable": user.transfer_enable,
            "device_limit": user.device_limit,
            "email": user.email,
            "uuid": user.uuid,
            "alive_ip": alive_ip,
            "subscribe_url": await self.build_subscribe_url(user),
            "reset_day": _reset_day(user),
            "allow_new_period": await self.setting_service.get_int("allow_new_period", 0),
        }

    async def build_subscribe_url(self, user: User) -> str:
        """按配置生成订阅 URL，支持直连、一次性 token 和 TOTP token。"""
        method = await self.setting_service.get_int("show_subscribe_method", 0)
        path = await self.setting_service.get_str("subscribe_path", "/api/v1/client/subscribe")
        if not path:
            path = "/api/v1/client/subscribe"
        token = user.token

        if method == 1:
            cached = await self.cache.get(f"otp_{user.token}")
            if not cached:
                cached = _base64_urlsafe(secrets.token_bytes(24))
                added = await self.cache.set(f"otp_{user.token}", cached, ex=86400, nx=True)
                if added:
                    await self.cache.set(f"otpn_{cached}", user.token, ex=86400)
                else:
                    cached = await self.cache.get(f"otp_{user.token}")
            token = str(cached)
        elif method == 2:
            expire_minutes = await self.setting_service.get_int("show_subscribe_expire", 5)
            timestep = max(expire_minutes, 1) * 60
            counter = int(time.time() // timestep)
            counter_bytes = (0).to_bytes(4, "big") + counter.to_bytes(4, "big")
            digest = hmac.new(user.token.encode(), counter_bytes, hashlib.sha1).hexdigest()
            token = _base64_urlsafe(f"{user.id}:{digest}".encode())

        separator = "&" if "?" in path else "?"
        url_path = f"{path}{separator}token={urllib.parse.quote(token)}"
        base_url = await self._subscribe_base_url()
        return f"{base_url}{url_path}" if base_url else url_path

    async def resolve_subscribe_user(self, token: str) -> User:
        """解析订阅 token 并返回用户。"""
        if not token:
            raise UnauthorizedException("token is null")
        method = await self.setting_service.get_int("show_subscribe_method", 0)
        user_token = token
        if method == 1:
            raw = await self.cache.get(f"otpn_{token}")
            if raw is None:
                raise UnauthorizedException("token is error")
            user_token = str(raw)
            await self.cache.delete(f"otpn_{token}")
            await self.cache.delete(f"otp_{user_token}")
        elif method == 2:
            cached = await self.cache.get(f"totp_{token}")
            if cached is not None:
                user_token = str(cached)
            else:
                user_id, digest = _decode_totp_token(token)
                user = await self.user_repo.get_by_id(user_id)
                if user is None:
                    raise UnauthorizedException("token is error")
                expire_minutes = await self.setting_service.get_int("show_subscribe_expire", 5)
                timestep = max(expire_minutes, 1) * 60
                counter = int(time.time() // timestep)
                counter_bytes = (0).to_bytes(4, "big") + counter.to_bytes(4, "big")
                expected = hmac.new(user.token.encode(), counter_bytes, hashlib.sha1).hexdigest()
                if not hmac.compare_digest(expected, digest):
                    raise UnauthorizedException("token is error")
                user_token = user.token
                await self.cache.set(f"totp_{token}", user_token, ex=timestep)

        user = await self.user_repo.get_by_token(user_token)
        if user is None:
            raise UnauthorizedException("token is error")
        return user

    async def get_available_servers(self, user: User) -> list[dict[str, Any]]:
        """获取用户可用节点。"""
        if not self.is_available(user):
            return []
        nodes = await self.node_repo.list_visible_by_group(user.group_id)
        servers = [_node_to_subscribe_dict(node, user.uuid) for node in nodes]
        if await self.setting_service.get_int("show_info_to_server_enable", 0):
            servers = _prepend_subscribe_info_servers(servers, user)
        return servers

    async def render_subscription(self, user: User, flag: str | None = None) -> tuple[str, str, dict[str, str]]:
        """根据客户端标识渲染订阅内容。"""
        if not self.is_available(user):
            raise ForbiddenException("订阅不可用")

        app_name = await self.setting_service.get_str("app_name", "PyBoard")
        app_url = await self.setting_service.get_str("app_url", "")
        subscribe_format = _detect_format(flag)
        servers = await self.get_available_servers(user)
        if subscribe_format == "sagernet":
            servers = [server for server in servers if server["protocol"] != "hysteria"]

        context = {
            "app_name": app_name,
            "app_url": app_url,
            "subscribe_url": await self.build_subscribe_url(user),
            "format": subscribe_format,
            "singbox_old": subscribe_format == "singbox_old",
            "user": _user_to_subscribe_dict(user),
            "servers": servers,
        }
        headers = _subscription_headers(user, app_name, app_url)
        template, media_type = _template_for_format(subscribe_format)

        if subscribe_format in {"singbox", "singbox_old"}:
            headers["profile-title"] = "base64:" + base64.b64encode(app_name.encode()).decode()
        elif subscribe_format in {"surge", "surfboard"}:
            headers["content-disposition"] = f"attachment;filename*=UTF-8''{urllib.parse.quote(app_name)}.conf"
        elif subscribe_format == "v2raytun":
            headers["profile-title"] = app_name
            headers["content-disposition"] = f'attachment; filename="{app_name}"'

        content = _render(template, **context)
        if subscribe_format in _BASE64_FORMATS:
            content = base64.b64encode(content.encode()).decode()
        return content, media_type, headers

    def is_available(self, user: User) -> bool:
        """账号是否可用于订阅。"""
        now = int(time.time())
        not_expired = user.expired_at is None or user.expired_at > now
        return bool(
            not user.banned
            and user.plan_id
            and user.transfer_enable > 0
            and (user.u + user.d) < user.transfer_enable
            and not_expired
        )

    async def _get_user(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        return user

    async def _subscribe_base_url(self) -> str:
        subscribe_urls = await self.setting_service.get_str("subscribe_url", "")
        if subscribe_urls:
            candidates = [item.strip().rstrip("/") for item in subscribe_urls.split(",") if item.strip()]
            if candidates:
                return candidates[0]
        return (await self.setting_service.get_str("app_url", "")).rstrip("/")


def build_uri(uuid: str, server: dict[str, Any]) -> str:
    """用通用 URI 模板渲染单个节点，保留给内部或测试复用。"""
    prepared = _prepare_subscribe_server(server, uuid)
    return _render("subscribe/uri.txt.j2", user={"uuid": uuid}, server=prepared).strip()


def _render(template_name: str, **context: Any) -> str:
    return _env.get_template(template_name).render(**context)


def _template_for_format(subscribe_format: str) -> tuple[str, str]:
    if subscribe_format in _CLASH_FORMATS:
        return "subscribe/clash.yaml.j2", "text/yaml; charset=utf-8"
    if subscribe_format in {"singbox", "singbox_old"}:
        return "subscribe/singbox.json.j2", "application/json; charset=utf-8"
    if subscribe_format == "shadowsocks":
        return "subscribe/sip008.json.j2", "application/json; charset=utf-8"
    if subscribe_format == "surge":
        return "subscribe/surge.conf.j2", "text/plain; charset=utf-8"
    if subscribe_format == "surfboard":
        return "subscribe/surfboard.conf.j2", "text/plain; charset=utf-8"
    if subscribe_format in {"loon", "quantumultx", "shadowrocket"}:
        return "subscribe/client_lines.txt.j2", "text/plain; charset=utf-8"
    return "subscribe/general.txt.j2", "text/plain; charset=utf-8"


def _node_to_subscribe_dict(node: ServerV2Node, uuid: str) -> dict[str, Any]:
    return _prepare_subscribe_server(
        {
            "id": node.id,
            "type": "v2node",
            "protocol": node.protocol,
            "name": node.name,
            "host": node.host,
            "port": node.port,
            "server_port": node.server_port,
            "rate": node.rate,
            "network": node.network,
            "network_settings": _json_cast(node.network_settings) or {},
            "tls": node.tls,
            "tls_settings": _json_cast(node.tls_settings) or {},
            "flow": node.flow,
            "encryption": node.encryption,
            "encryption_settings": _json_cast(node.encryption_settings) or {},
            "cipher": node.cipher,
            "obfs": node.obfs,
            "obfs_password": node.obfs_password,
            "up_mbps": node.up_mbps,
            "down_mbps": node.down_mbps,
            "disable_sni": node.disable_sni,
            "udp_relay_mode": node.udp_relay_mode,
            "zero_rtt_handshake": node.zero_rtt_handshake,
            "congestion_control": node.congestion_control,
            "padding_scheme": _json_cast(node.padding_scheme) or {},
            "created_at": node.created_at,
            "updated_at": node.updated_at,
            "cache_key": f"v2node:{node.id}:{node.updated_at}",
        },
        uuid,
    )


def _prepare_subscribe_server(server: dict[str, Any], uuid: str) -> dict[str, Any]:
    server = dict(server)
    protocol = str(server.get("protocol") or server.get("type") or "")
    network = str(server.get("network") or "tcp")
    tls_settings = _dict_or_empty(server.get("tls_settings") or server.get("tlsSettings"))
    network_settings = _dict_or_empty(server.get("network_settings") or server.get("networkSettings"))
    first_port = _first_port(str(server.get("port") or ""))
    allow_insecure = _allow_insecure(server, tls_settings)
    sni = str(server.get("server_name") or tls_settings.get("server_name") or tls_settings.get("serverName") or "")
    ss_password = _ss_password(uuid, server)

    server.update(
        {
            "protocol": protocol,
            "network": network,
            "tls_settings": tls_settings,
            "network_settings": network_settings,
            "formatted_host": _format_host(str(server.get("host") or "")),
            "first_port": first_port,
            "first_port_int": _safe_int(first_port),
            "allow_insecure": allow_insecure,
            "allow_insecure_int": int(allow_insecure),
            "sni": sni,
            "ss_password": ss_password,
            "ss_auth": _base64_urlsafe(f"{server.get('cipher') or 'none'}:{ss_password}".encode()),
            "ss_plugin": _ss_plugin(server, network_settings),
            "sip008": protocol == "shadowsocks" and server.get("cipher") in _SS_SIP008_CIPHERS,
            "vless_encryption": _vless_encryption(server),
            "multi_port": "," in str(server.get("port") or "") or "-" in str(server.get("port") or ""),
        }
    )
    return server


def _user_to_subscribe_dict(user: User) -> dict[str, Any]:
    upload_gb = round(user.u / (1024 * 1024 * 1024), 2)
    download_gb = round(user.d / (1024 * 1024 * 1024), 2)
    total_gb = round(user.transfer_enable / (1024 * 1024 * 1024), 2)
    expired_date = "长期有效" if user.expired_at is None else time.strftime("%Y-%m-%d", time.localtime(user.expired_at))
    expired_at_text = "长期有效" if user.expired_at is None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user.expired_at))
    return {
        "id": user.id,
        "email": user.email,
        "uuid": user.uuid,
        "u": user.u,
        "d": user.d,
        "transfer_enable": user.transfer_enable,
        "expired_at": user.expired_at,
        "upload_gb": upload_gb,
        "download_gb": download_gb,
        "used_gb": round(upload_gb + download_gb, 2),
        "total_gb": total_gb,
        "expired_date": expired_date,
        "expired_at_text": expired_at_text,
    }


def _plan_to_dict(plan: Plan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "name": plan.name,
        "group_id": plan.group_id,
        "transfer_enable": plan.transfer_enable,
        "device_limit": plan.device_limit,
        "speed_limit": plan.speed_limit,
    }


def _prepend_subscribe_info_servers(servers: list[dict[str, Any]], user: User) -> list[dict[str, Any]]:
    if not servers:
        return servers
    remaining = _format_bytes(user.transfer_enable - user.u - user.d)
    expired = "长期有效" if user.expired_at is None else time.strftime("%Y-%m-%d", time.localtime(user.expired_at))
    result = [
        {**servers[0], "name": f"剩余流量：{remaining}"},
        {**servers[0], "name": f"套餐到期：{expired}"},
    ]
    reset_day = _reset_day(user)
    if reset_day:
        result.append({**servers[0], "name": f"距离下次重置剩余：{reset_day} 天"})
    return result + servers


def _detect_format(flag: str | None) -> str:
    value = urllib.parse.unquote((flag or "").lower())
    if "sing-box" in value:
        version = _extract_singbox_version(value)
        return "singbox" if version and _version_gte(version, "1.12.0") else "singbox_old"
    checks = [
        ("singbox", ("sing",)),
        ("clash_meta", ("clash.meta", "clash-meta", "mihomo", "meta")),
        ("clash_verge", ("clash-verge", "verge")),
        ("clash_nyanpasu", ("nyanpasu",)),
        ("stash", ("stash",)),
        ("clash", ("clash",)),
        ("shadowrocket", ("shadowrocket",)),
        ("quantumultx", ("quantumult x", "quantumult%20x", "quantumultx")),
        ("surfboard", ("surfboard",)),
        ("surge", ("surge",)),
        ("loon", ("loon",)),
        ("shadowsocks", ("shadowsocks", "sip008")),
        ("sagernet", ("sagernet",)),
        ("passwall", ("passwall",)),
        ("ssrplus", ("ssrplus",)),
        ("v2raytun", ("v2raytun",)),
        ("v2rayng", ("v2rayng",)),
        ("v2rayn", ("v2rayn",)),
    ]
    for name, needles in checks:
        if any(needle in value for needle in needles):
            return name
    return "general"


def _extract_singbox_version(value: str) -> str | None:
    parts = value.replace("/", " ").split()
    for index, part in enumerate(parts):
        if part == "sing-box" and index + 1 < len(parts):
            return parts[index + 1]
        if part.startswith("sing-box"):
            maybe = part.removeprefix("sing-box").strip("/")
            if maybe:
                return maybe
    return None


def _version_gte(version: str, target: str) -> bool:
    def parse(item: str) -> tuple[int, ...]:
        nums: list[int] = []
        for part in item.split("."):
            digits = "".join(char for char in part if char.isdigit())
            nums.append(int(digits or 0))
        return tuple(nums)

    left = parse(version)
    right = parse(target)
    size = max(len(left), len(right))
    return left + (0,) * (size - len(left)) >= right + (0,) * (size - len(right))


def _subscription_headers(user: User, app_name: str, app_url: str) -> dict[str, str]:
    headers = {
        "subscription-userinfo": (
            f"upload={user.u}; download={user.d}; total={user.transfer_enable}; expire={user.expired_at}"
        ),
        "profile-update-interval": "24",
        "content-disposition": f"attachment;filename*=UTF-8''{urllib.parse.quote(app_name)}",
    }
    if app_url:
        headers["profile-web-page-url"] = app_url
    return headers


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _allow_insecure(server: dict[str, Any], tls_settings: dict[str, Any]) -> bool:
    return bool(
        server.get("insecure")
        or server.get("allow_insecure")
        or tls_settings.get("allow_insecure")
        or tls_settings.get("allowInsecure")
    )


def _ss_password(uuid: str, server: dict[str, Any]) -> str:
    cipher = str(server.get("cipher") or "")
    if "2022-blake3" not in cipher:
        return uuid
    length = 16 if cipher == "2022-blake3-aes-128-gcm" else 32
    return f"{_get_server_key(int(server.get('created_at') or 0), length)}:{_uuid_to_base64(uuid, length)}"


def _ss_plugin(server: dict[str, Any], network_settings: dict[str, Any]) -> str:
    if server.get("obfs") == "http":
        host = server.get("obfs_host") or server.get("obfs-host") or ""
        path = server.get("obfs_path") or server.get("obfs-path") or "/"
        return f"obfs-local;obfs=http;obfs-host={host};path={path}"
    host = network_settings.get("Host") or (network_settings.get("headers") or {}).get("Host")
    if str(server.get("network") or "") == "http" and host:
        return f"obfs-local;obfs=http;obfs-host={host};path={network_settings.get('path') or '/'}"
    return ""


def _vless_encryption(server: dict[str, Any]) -> str:
    settings = _dict_or_empty(server.get("encryption_settings"))
    if server.get("encryption") != "mlkem768x25519plus" or not settings:
        return ""
    parts = ["mlkem768x25519plus", str(settings.get("mode") or "native"), str(settings.get("rtt") or "1rtt")]
    if settings.get("client_padding"):
        parts.append(str(settings["client_padding"]))
    parts.append(str(settings.get("password") or ""))
    return ".".join(parts)


def _json_cast(value: Any) -> Any:
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


def _decode_totp_token(token: str) -> tuple[int, str]:
    try:
        decoded = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode()
        user_id, digest = decoded.split(":", 1)
        return int(user_id), digest
    except (ValueError, UnicodeDecodeError):
        raise UnauthorizedException("token is error") from None


def _base64_urlsafe(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _uuid_to_base64(uuid: str, length: int) -> str:
    return base64.b64encode(uuid[:length].encode()).decode()


def _get_server_key(timestamp: int, length: int) -> str:
    return base64.b64encode(hashlib.md5(str(timestamp).encode()).hexdigest()[:length].encode()).decode()


def _format_host(host: str) -> str:
    try:
        return f"[{host}]" if ipaddress.ip_address(host).version == 6 else host
    except ValueError:
        return host


def _first_port(port: str) -> str:
    first = str(port).split(",", 1)[0]
    return first.split("-", 1)[0]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_bytes(value: int) -> str:
    size = float(max(value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.2f} PB"


def _reset_day(user: User) -> int | None:
    # 当前模型没有保存套餐周期起算日，先返回 None；保留字段兼容前端。
    _ = user
    return None


async def _cache_get_json(cache: RuntimeCache, key: str) -> Any:
    raw = await cache.get(key)
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return orjson.loads(raw)
    except (orjson.JSONDecodeError, TypeError):
        return None
