"""CommissionLog 字段全集，不含 id/关系/系统字段。对应 佣金记录表 `commission_log`。"""

from sqlmodel import Field, SQLModel


class CommissionLogBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    invite_user_id: int  # 邀请人用户 ID
    user_id: int  # 被邀请人用户 ID
    trade_no: str = Field(max_length=36, unique=True)  # 关联订单号
    order_amount: int  # 订单金额
    get_amount: int  # 获得佣金金额
