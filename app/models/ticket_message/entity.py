"""TicketMessage 数据库实体。对应 工单消息表 `ticket_message`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.ticket_message.base import TicketMessageBase


class TicketMessage(TicketMessageBase, table=True):
    __tablename__ = "ticket_message"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
