"""PostgreSQL 队列任务实体。"""

from sqlmodel import Field

from app.models._columns import created_at_field, updated_at_field
from app.models.queue_job.base import QueueJobBase


class QueueJob(QueueJobBase, table=True):
    __tablename__ = "queue_job"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
