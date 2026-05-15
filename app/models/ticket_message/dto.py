"""TicketMessage DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class TicketMessagePublic(SQLModel):
    """工单消息列表公开视图。"""

    id: int
    user_id: int
    ticket_id: int
    message: str
    is_me: bool | None = None
    created_at: int


class TicketMessageRead(SQLModel):
    """工单消息详情视图。"""

    id: int
    user_id: int
    ticket_id: int
    message: str
    created_at: int
    updated_at: int
