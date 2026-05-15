"""FailedJob DTO，接口视图，不做持久化。"""

from typing import Any

from sqlmodel import SQLModel


class FailedJobPublic(SQLModel):
    """失败队列任务列表公开视图。"""

    id: int
    connection: str
    queue: str
    failed_at: str
    created_at: int


class FailedJobRead(SQLModel):
    """失败队列任务详情视图。"""

    id: int
    connection: str
    queue: str
    payload: Any
    exception: str
    failed_at: str
    created_at: int
    updated_at: int
