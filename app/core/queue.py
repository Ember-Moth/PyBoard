"""PostgreSQL 队列客户端。"""

import time
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_engine
from app.models.queue_job.entity import QueueJob

_queue: "PostgresQueue | None" = None


class PostgresQueue:
    """最小队列客户端，提供与业务代码使用点兼容的 enqueue_job。"""

    def __init__(self, default_queue_name: str | None = None):
        self.default_queue_name = default_queue_name or settings.queue_default_name

    async def enqueue_job(self, job_name: str, *args: Any, **kwargs: Any) -> int | None:
        queue_name = str(kwargs.pop("_queue_name", self.default_queue_name))
        job_key = kwargs.pop("_job_id", None)
        scheduled_at = _scheduled_at(kwargs)
        payload = {
            "queue": queue_name,
            "job_name": job_name,
            "job_key": str(job_key) if job_key else None,
            "args": list(args),
            "kwargs": kwargs,
            "status": "pending",
            "attempts": 0,
            "max_tries": settings.queue_max_tries,
            "scheduled_at": scheduled_at,
        }
        engine = get_engine()
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
        async with session_factory() as db:  # type: ignore[operator]
            stmt = insert(QueueJob).values(**payload).returning(QueueJob.id)
            if job_key:
                stmt = stmt.on_conflict_do_nothing(index_elements=[QueueJob.job_key])
            result = await db.execute(stmt)
            await db.commit()
            inserted_id = result.scalar_one_or_none()
            return int(inserted_id) if inserted_id is not None else None

    async def close(self) -> None:
        return None


async def get_queue() -> PostgresQueue:
    """获取 PostgreSQL 队列客户端。"""
    global _queue
    if _queue is None:
        _queue = PostgresQueue()
    return _queue


async def close_queue() -> None:
    """应用关闭时释放队列客户端。"""
    global _queue
    if _queue is not None:
        await _queue.close()
        _queue = None


def _scheduled_at(kwargs: dict[str, Any]) -> int:
    defer_until = kwargs.pop("_defer_until", None)
    defer_by = kwargs.pop("_defer_by", None)
    if defer_until is not None:
        if hasattr(defer_until, "timestamp"):
            return int(defer_until.timestamp())
        return int(defer_until)
    if defer_by is not None:
        return int(time.time() + float(defer_by))
    return int(time.time())
