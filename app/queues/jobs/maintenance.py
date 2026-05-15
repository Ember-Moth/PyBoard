"""周期性维护任务，对齐原版 Console Commands。"""

import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.core.database import get_engine
from app.models.order.entity import Order
from app.queues.jobs.pg_cache import flush_traffic_cache_to_users
from app.queues.jobs.stat import aggregate_stats
from app.queues.names import QUEUE_ORDER_HANDLE
from app.services.log_event import cleanup_log_events_by_retention, create_log_event


async def traffic_update(ctx: dict) -> None:
    """把 PostgreSQL UNLOGGED cache 中的累计流量原子落库到 users.u/d。"""
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        async with db.begin():
            await flush_traffic_cache_to_users(db)


async def check_order(ctx: dict) -> None:
    """扫描待处理订单并投递 order_handle。"""
    queue = ctx.get("queue")
    if queue is None or not hasattr(queue, "enqueue_job"):
        return

    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        result = await db.execute(select(Order).where(Order.status.in_([0, 1])).order_by(Order.created_at.asc()))  # type: ignore[attr-defined]
        for order in result.scalars().all():
            await queue.enqueue_job(
                "order_handle",
                order.trade_no,
                _queue_name=QUEUE_ORDER_HANDLE,
                _job_id=f"order_handle:{order.trade_no}",
            )


async def aggregate_yesterday_stats(ctx: dict) -> None:
    """聚合昨日站点统计。"""
    today = _today_timestamp()
    await aggregate_stats(ctx, "d", today - 86400)


async def cleanup_log_events(ctx: dict) -> None:
    """按分类保留策略清理可清理日志。"""
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        async with db.begin():
            deleted = await cleanup_log_events_by_retention(db)
            await create_log_event(
                db,
                category="system",
                event="log.cleanup",
                message="日志保留策略清理完成",
                data={"deleted": deleted},
            )


def _today_timestamp() -> int:
    now = int(time.time())
    return now - (now % 86400)
