"""Ticket DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class TicketPublic(SQLModel):
    """工单列表公开视图。"""

    id: int
    user_id: int
    subject: str
    level: int
    status: int
    reply_status: int
    created_at: int


class TicketRead(SQLModel):
    """工单详情视图。"""

    id: int
    user_id: int
    subject: str
    level: int
    status: int
    reply_status: int
    created_at: int
    updated_at: int


class TicketCreate(SQLModel):
    """创建工单。"""

    subject: str
    level: int = 0
    message: str


class TicketReply(SQLModel):
    """回复工单。"""

    message: str


class TicketClose(SQLModel):
    """关闭工单。"""

    id: int


class TicketWithdraw(SQLModel):
    """佣金提现工单。"""

    withdraw_method: str
    withdraw_account: str
