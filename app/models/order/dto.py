"""Order DTO，接口视图，不做持久化。"""

from typing import Any

from sqlmodel import SQLModel


class OrderPublic(SQLModel):
    """订单列表公开视图（用户端）。"""

    id: int
    plan_id: int
    period: str
    trade_no: str
    total_amount: int
    status: int
    paid_at: int | None
    created_at: int


class OrderRead(SQLModel):
    """订单详情视图（用户端）。"""

    id: int
    plan_id: int
    period: str
    trade_no: str
    total_amount: int
    handling_amount: int | None
    balance_amount: int | None
    status: int
    paid_at: int | None
    created_at: int
    updated_at: int


class OrderDetailWithPlan(SQLModel):
    """订单详情带套餐信息。"""

    order: OrderRead
    plan: dict[str, Any] | None


class OrderCreate(SQLModel):
    """创建订单请求。"""

    plan_id: int
    period: str
    coupon_code: str | None = None
    deposit_amount: int | None = None


class OrderCheckout(SQLModel):
    """订单结账请求。"""

    trade_no: str
    method: int


class OrderStatus(SQLModel):
    """订单状态响应。"""

    status: int


class PaymentMethodPublic(SQLModel):
    """支付方式公开视图。"""

    id: int
    name: str
    payment: str
    icon: str | None
    handling_fee_fixed: int | None
    handling_fee_percent: float | None


class PaymentResult(SQLModel):
    """支付结果响应。"""

    type: int  # 0:二维码 1:跳转URL
    data: str | bool


class OrderCancel(SQLModel):
    """取消订单请求。"""

    trade_no: str


class AdminOrderUpdate(SQLModel):
    """管理端更新订单。"""

    trade_no: str
    commission_status: int | None = None


class AdminOrderTradeNo(SQLModel):
    """管理端按交易号操作订单。"""

    trade_no: str


class AdminOrderAssign(SQLModel):
    """管理端给用户分配订单。"""

    email: str
    plan_id: int
    period: str
    total_amount: int = 0
