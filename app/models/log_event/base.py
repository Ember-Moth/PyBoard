"""统一日志事件字段。"""

from typing import Any

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel

from app.models._columns import jsonb_field


class LogEventBase(SQLModel):
    """运行日志、请求日志、审计日志和队列日志统一结构。"""

    level: str = Field(default="info", max_length=16, index=True)
    category: str = Field(default="access", max_length=32, index=True)
    event: str = Field(max_length=64, index=True)
    message: str = Field(max_length=255)

    request_id: str | None = Field(default=None, max_length=64, index=True)
    trace_id: str | None = Field(default=None, max_length=64)

    actor_type: str | None = Field(default=None, max_length=32)
    actor_id: int | None = Field(default=None, index=True)
    target_type: str | None = Field(default=None, max_length=32)
    target_id: str | None = Field(default=None, max_length=64)

    method: str | None = Field(default=None, max_length=11)
    path: str | None = Field(default=None, max_length=255)
    status_code: int | None = None
    duration_ms: int | None = None
    ip: str | None = Field(default=None, max_length=128)
    user_agent: str | None = Field(default=None, max_length=255)

    data: Any = jsonb_field()
    error_type: str | None = Field(default=None, max_length=128)
    error_stack: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
