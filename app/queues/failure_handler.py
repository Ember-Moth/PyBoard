"""任务失败记录 —— 持久化到 failed_jobs 表。"""

import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_engine
from app.models.failed_job.entity import FailedJob
from app.services.log_event import create_log_event


async def record_failed_job(
    *,
    queue: str,
    job_id: int | str | None,
    job_name: str,
    args: list,
    kwargs: dict,
    exc: BaseException,
) -> None:
    """记录 PostgreSQL 队列任务失败。"""
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        try:
            failed = FailedJob(
                connection="postgresql",
                queue=queue,
                payload={
                    "job_id": job_id,
                    "job_name": job_name,
                    "args": args,
                    "kwargs": kwargs,
                },
                exception=str(exc),
                failed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            db.add(failed)
            await db.flush()
            await create_log_event(
                db,
                level="error",
                category="queue",
                event="queue.failed",
                message=f"队列任务失败：{job_name}",
                target_type="queue_job",
                target_id=str(job_id),
                data={
                    "connection": "postgresql",
                    "queue": queue,
                    "job_id": job_id,
                    "job_name": job_name,
                    "args": args,
                    "kwargs": kwargs,
                    "failed_job_id": failed.id,
                },
                error_type=type(exc).__name__,
                error_stack=str(exc),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
