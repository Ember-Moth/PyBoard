"""Stat DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class StatPublic(SQLModel):
    """订单统计列表公开视图。"""

    id: int
    created_at: int


class StatRead(SQLModel):
    """订单统计详情视图。"""

    id: int
    record_at: int
    record_type: str
    order_count: int
    order_total: int
    commission_count: int
    commission_total: int
    paid_count: int
    paid_total: int
    register_count: int
    invite_count: int
    transfer_used_total: str
    created_at: int
    updated_at: int
