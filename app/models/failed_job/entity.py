"""FailedJob 数据库实体。对应 失败队列任务表 `failed_jobs`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.failed_job.base import FailedJobBase


class FailedJob(FailedJobBase, table=True):
    __tablename__ = "failed_jobs"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
