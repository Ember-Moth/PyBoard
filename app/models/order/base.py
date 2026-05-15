"""Order 字段全集，不含 id/关系/系统字段。对应 订单表 `orders`。"""

from sqlmodel import Field, SQLModel


class OrderBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    invite_user_id: int | None = None  # 邀请人用户 ID
    user_id: int = Field(index=True)  # 下单用户 ID
    plan_id: int  # 订购套餐 ID
    coupon_id: int | None = None  # 使用优惠券 ID
    payment_id: int | None = None  # 支付方式 ID
    type: int  # 1-新购 2-续费 3-升级
    period: str = Field(max_length=255)  # 订阅周期
    trade_no: str = Field(max_length=36, unique=True)  # 本地交易单号
    callback_no: str | None = Field(default=None, max_length=255)  # 支付回调单号
    total_amount: int  # 订单总金额
    handling_amount: int | None = None  # 手续费金额
    discount_amount: int | None = None  # 优惠金额
    surplus_amount: int | None = None  # 剩余价值(升级时折抵)
    refund_amount: int | None = None  # 退款金额
    balance_amount: int | None = None  # 使用余额金额
    surplus_order_ids: str | None = None  # 折抵订单 ID 列表
    status: int = 0  # 0-待支付 1-开通中 2-已取消 3-已完成 4-已折抵
    commission_status: int = 0  # 佣金状态 0-待确认 1-发放中 2-有效 3-无效
    commission_balance: int = 0  # 佣金金额
    actual_commission_balance: int | None = None  # 实际支付佣金
    paid_at: int | None = None  # 支付时间
