"""FailedJob 字段全集，不含 id/关系/系统字段。对应 失败队列任务表 `failed_jobs`。"""

from typing import Any

from sqlmodel import SQLModel

from app.models._columns import jsonb_object_field


class FailedJobBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    connection: str  # 队列连接名
    queue: str  # 队列名
    payload: dict[str, Any] = jsonb_object_field()  # 任务载荷
    exception: str  # 异常信息
    failed_at: str  # 失败时间
