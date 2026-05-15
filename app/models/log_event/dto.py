"""统一日志事件 DTO。"""

from typing import Any

from sqlmodel import SQLModel


class LogEventPublic(SQLModel):
    id: int
    level: str
    category: str
    event: str
    message: str
    request_id: str | None
    actor_type: str | None
    actor_id: int | None
    target_type: str | None
    target_id: str | None
    method: str | None
    path: str | None
    status_code: int | None
    duration_ms: int | None
    ip: str | None
    created_at: int


class LogEventRead(SQLModel):
    id: int
    level: str
    category: str
    event: str
    message: str
    request_id: str | None
    trace_id: str | None
    actor_type: str | None
    actor_id: int | None
    target_type: str | None
    target_id: str | None
    method: str | None
    path: str | None
    status_code: int | None
    duration_ms: int | None
    ip: str | None
    user_agent: str | None
    data: Any
    error_type: str | None
    error_stack: str | None
    created_at: int
    updated_at: int
