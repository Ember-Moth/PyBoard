"""支付网关注册表。"""

import json
from typing import Any

from app.core.exceptions import BadRequestException
from app.payments.base import PaymentGateway

_GATEWAYS: dict[str, type[PaymentGateway]] = {}


def _key(name: str) -> str:
    return name.strip().lower()


def register_payment_gateway(gateway_cls: type[PaymentGateway]) -> None:
    """注册支付网关类。"""
    names = {gateway_cls.gateway, gateway_cls.gateway.lower(), *gateway_cls.aliases}
    for name in names:
        _GATEWAYS[_key(name)] = gateway_cls


def get_payment_gateway(name: str) -> type[PaymentGateway]:
    """按名称获取支付网关类。"""
    gateway_cls = _GATEWAYS.get(_key(name))
    if gateway_cls is None:
        raise BadRequestException("支付网关不存在")
    return gateway_cls


def parse_config(config: str | dict[str, Any] | None) -> dict[str, Any]:
    """解析支付配置。"""
    if config is None or config == "":
        raise BadRequestException("支付配置不能为空")
    if isinstance(config, dict):
        return config
    try:
        parsed = json.loads(config)
    except json.JSONDecodeError:
        raise BadRequestException("支付配置必须是合法 JSON") from None
    if not isinstance(parsed, dict):
        raise BadRequestException("支付配置必须是 JSON 对象")
    return parsed


def validate_gateway_config(name: str, config: str | dict[str, Any] | None) -> dict[str, Any]:
    """校验指定网关配置。"""
    gateway_cls = get_payment_gateway(name)
    return gateway_cls.validate_config(parse_config(config))


def create_payment_gateway(name: str, config: str | dict[str, Any] | None) -> PaymentGateway:
    """创建支付网关实例。"""
    gateway_cls = get_payment_gateway(name)
    parsed = gateway_cls.validate_config(parse_config(config))
    return gateway_cls(parsed)


def canonical_gateway_name(name: str) -> str:
    """返回网关规范名称。"""
    return get_payment_gateway(name).gateway


def route_gateway_name(name: str) -> str:
    """返回回调路径使用的网关名称。"""
    gateway_cls = get_payment_gateway(name)
    return gateway_cls.aliases[0] if gateway_cls.aliases else gateway_cls.gateway.lower()


def list_payment_gateways() -> list[dict[str, Any]]:
    """列出当前后端支持的支付网关。"""
    seen: set[type[PaymentGateway]] = set()
    gateways: list[dict[str, Any]] = []
    for gateway_cls in _GATEWAYS.values():
        if gateway_cls in seen:
            continue
        seen.add(gateway_cls)
        gateways.append(
            {
                "payment": gateway_cls.gateway,
                "name": gateway_cls.label,
                "route": route_gateway_name(gateway_cls.gateway),
                "form": gateway_cls.form(),
            }
        )
    return sorted(gateways, key=lambda item: item["payment"])


from app.payments.epay import EPay  # noqa: E402

register_payment_gateway(EPay)
