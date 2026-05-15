"""统一日志事件实体。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field

from app.models.log_event.base import LogEventBase


class LogEvent(LogEventBase, table=True):
    __tablename__ = "log_event"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field(index=True)
    updated_at: int | None = updated_at_field()
