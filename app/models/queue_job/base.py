"""PostgreSQL 队列任务字段。"""

from typing import Any

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel

from app.models._columns import jsonb_array_field, jsonb_object_field


class QueueJobBase(SQLModel):
    """队列任务由 PostgreSQL 表承载，Worker 通过 SKIP LOCKED 领取。"""

    queue: str = Field(default="default", max_length=64, index=True)
    job_name: str = Field(max_length=128, index=True)
    job_key: str | None = Field(default=None, max_length=255, unique=True)
    args: list[Any] = jsonb_array_field()
    kwargs: dict[str, Any] = jsonb_object_field()
    status: str = Field(default="pending", max_length=16, index=True)
    attempts: int = 0
    max_tries: int = 3
    scheduled_at: int = Field(default=0, index=True, sa_type=BigInteger)
    reserved_at: int | None = Field(default=None, index=True, sa_type=BigInteger)
    finished_at: int | None = Field(default=None, index=True, sa_type=BigInteger)
    failed_at: int | None = Field(default=None, index=True, sa_type=BigInteger)
    last_error: str | None = None
