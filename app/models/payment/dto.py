"""Payment DTO，接口视图，不做持久化。"""

from typing import Any

from sqlmodel import SQLModel


class PaymentPublic(SQLModel):
    """支付方式列表公开视图。"""

    id: int
    created_at: int


class PaymentRead(SQLModel):
    """支付方式详情视图。"""

    id: int
    uuid: str
    payment: str
    name: str
    icon: str | None
    config: dict[str, Any]
    notify_domain: str | None
    handling_fee_fixed: int | None
    handling_fee_percent: float | None
    enable: bool
    sort: int | None
    created_at: int
    updated_at: int


class PaymentCreate(SQLModel):
    """创建支付方式。"""

    payment: str = "EPay"  # 支付网关标识
    name: str
    icon: str | None = None
    config: str | dict[str, Any]  # JSON 配置
    notify_domain: str | None = None
    handling_fee_fixed: int | None = None
    handling_fee_percent: float | None = None
    enable: bool = False
    sort: int | None = None


class PaymentUpdate(SQLModel):
    """更新支付方式。"""

    payment: str | None = None
    name: str | None = None
    icon: str | None = None
    config: str | dict[str, Any] | None = None
    notify_domain: str | None = None
    handling_fee_fixed: int | None = None
    handling_fee_percent: float | None = None
    enable: bool | None = None
    sort: int | None = None
