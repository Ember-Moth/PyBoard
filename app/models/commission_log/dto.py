"""CommissionLog DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class CommissionLogPublic(SQLModel):
    """佣金记录列表公开视图。"""

    id: int
    invite_user_id: int
    user_id: int
    trade_no: str
    order_amount: int
    get_amount: int
    created_at: int


class CommissionLogRead(SQLModel):
    """佣金记录详情视图。"""

    id: int
    invite_user_id: int
    user_id: int
    trade_no: str
    order_amount: int
    get_amount: int
    created_at: int
    updated_at: int


class CommissionTransfer(SQLModel):
    """佣金划转到余额。"""

    amount: int


class CommissionSummary(SQLModel):
    """邀请返利概览。"""

    codes: list
    stat: list[int]
