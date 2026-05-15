"""支付网关抽象。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.core.exceptions import BadRequestException


@dataclass(frozen=True)
class PaymentRequest:
    """发起支付所需的标准参数。"""

    trade_no: str
    total_amount: int
    notify_url: str
    return_url: str
    user_id: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentNotifyResult:
    """支付回调验证结果。"""

    success: bool
    trade_no: str = ""
    callback_no: str = ""
    paid_amount: int | None = None


class PaymentGateway(ABC):
    """支付网关基类。"""

    gateway: ClassVar[str]
    label: ClassVar[str]
    aliases: ClassVar[tuple[str, ...]] = ()
    required_config: ClassVar[tuple[str, ...]] = ()

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @property
    def route_name(self) -> str:
        """回调 URL 中使用的网关标识。"""
        return self.aliases[0] if self.aliases else self.gateway.lower()

    @classmethod
    def form(cls, config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        """返回管理端配置表单结构。"""
        return {}

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        """校验并标准化配置。"""
        missing = [key for key in cls.required_config if not config.get(key)]
        if missing:
            raise BadRequestException(f"支付配置缺少字段: {', '.join(missing)}")
        return config

    @abstractmethod
    def pay(self, request: PaymentRequest) -> dict[str, Any]:
        """生成支付请求结果。"""
        pass

    @abstractmethod
    def verify_notify(self, params: dict[str, Any]) -> PaymentNotifyResult:
        """验证支付回调并返回标准结果。"""
        pass
