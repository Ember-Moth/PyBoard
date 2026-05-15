"""Ticket 数据库实体。对应 工单表 `ticket`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.ticket.base import TicketBase


class Ticket(TicketBase, table=True):
    __tablename__ = "ticket"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
