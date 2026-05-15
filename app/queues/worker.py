"""PostgreSQL 队列 Worker。

启动方式：
    uv run python -m app.queues.worker

指定队列：
    uv run python -m app.queues.worker --queue traffic_fetch --queue stat
"""

import argparse
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_engine
from app.core.queue import PostgresQueue
from app.core.runtime import configure_async_runtime
from app.queues.failure_handler import record_failed_job
from app.queues.jobs import (
    aggregate_yesterday_stats,
    aggregate_stats,
    calc_commission,
    check_order,
    cleanup_log_events,
    order_handle,
    send_mail,
    send_telegram,
    stat_server,
    stat_user,
    traffic_fetch,
    traffic_update,
)
from app.queues.names import QUEUE_NAMES

ASYNC_RUNTIME = configure_async_runtime()

JobFunc = Callable[..., Awaitable[None]]

JOB_REGISTRY: dict[str, JobFunc] = {
    "send_mail": send_mail,
    "send_telegram": send_telegram,
    "order_handle": order_handle,
    "calc_commission": calc_commission,
    "aggregate_stats": aggregate_stats,
    "traffic_update": traffic_update,
    "check_order": check_order,
    "aggregate_yesterday_stats": aggregate_yesterday_stats,
    "cleanup_log_events": cleanup_log_events,
    "traffic_fetch": traffic_fetch,
    "stat_user": stat_user,
    "stat_server": stat_server,
}


async def run_worker(queues: list[str] | None = None, *, once: bool = False) -> None:
    queue_names = queues or [settings.queue_default_name]
    while True:
        jobs = await claim_jobs(queue_names, settings.queue_max_jobs)
        if not jobs and once:
            return
        if not jobs:
            await asyncio.sleep(settings.queue_poll_delay)
            continue
        await asyncio.gather(*(run_job(job) for job in jobs))


async def claim_jobs(queues: list[str], limit: int) -> list[dict[str, Any]]:
    engine = get_engine()
    now = int(time.time())
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                """
                WITH picked AS (
                    SELECT id
                    FROM queue_job
                    WHERE status = 'pending'
                      AND queue = ANY(:queues)
                      AND scheduled_at <= :now
                    ORDER BY scheduled_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT :limit
                )
                UPDATE queue_job AS job
                SET status = 'running',
                    attempts = job.attempts + 1,
                    reserved_at = :now
                FROM picked
                WHERE job.id = picked.id
                RETURNING job.id, job.queue, job.job_name, job.args, job.kwargs, job.attempts, job.max_tries
                """
            ),
            {"queues": queues, "now": now, "limit": limit},
        )
        return [dict(row._mapping) for row in result.all()]


async def run_job(job: dict[str, Any]) -> None:
    job_id = int(job["id"])
    queue_name = str(job["queue"])
    job_name = str(job["job_name"])
    args = list(job.get("args") or [])
    kwargs = dict(job.get("kwargs") or {})
    func = JOB_REGISTRY.get(job_name)
    if func is None:
        await fail_job(job, RuntimeError(f"未注册的队列任务：{job_name}"), retry=False)
        return

    ctx = {
        "job_id": job_id,
        "queue": PostgresQueue(queue_name),
    }
    try:
        await func(ctx, *args, **kwargs)
    except Exception as exc:
        await fail_job(job, exc, retry=bool(settings.queue_retry_jobs))
        return
    await finish_job(job_id)


async def finish_job(job_id: int) -> None:
    now = int(time.time())
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                UPDATE queue_job
                SET status = 'finished', finished_at = :now
                WHERE id = :job_id
                """
            ),
            {"job_id": job_id, "now": now},
        )


async def fail_job(job: dict[str, Any], exc: BaseException, *, retry: bool) -> None:
    now = int(time.time())
    job_id = int(job["id"])
    attempts = int(job.get("attempts") or 0)
    max_tries = int(job.get("max_tries") or settings.queue_max_tries)
    should_retry = retry and attempts < max_tries
    engine = get_engine()
    async with engine.begin() as conn:
        if should_retry:
            await conn.execute(
                text(
                    """
                    UPDATE queue_job
                    SET status = 'pending',
                        reserved_at = NULL,
                        scheduled_at = :scheduled_at,
                        last_error = :error
                    WHERE id = :job_id
                    """
                ),
                {"job_id": job_id, "scheduled_at": now + min(60, attempts * 5), "error": str(exc)},
            )
        else:
            await conn.execute(
                text(
                    """
                    UPDATE queue_job
                    SET status = 'failed',
                        failed_at = :now,
                        last_error = :error
                    WHERE id = :job_id
                    """
                ),
                {"job_id": job_id, "now": now, "error": str(exc)},
            )
    if not should_retry:
        await record_failed_job(
            queue=str(job["queue"]),
            job_id=job_id,
            job_name=str(job["job_name"]),
            args=list(job.get("args") or []),
            kwargs=dict(job.get("kwargs") or {}),
            exc=exc,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PostgreSQL queue worker")
    parser.add_argument("--queue", action="append", choices=QUEUE_NAMES, help="只消费指定队列，可重复传入")
    parser.add_argument("--once", action="store_true", help="只领取并执行一次，便于测试/运维")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_worker(args.queue, once=args.once))


if __name__ == "__main__":
    main()
