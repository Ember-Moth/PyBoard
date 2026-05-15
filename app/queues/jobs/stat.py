"""统计聚合任务。"""

import time
from calendar import monthrange

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.core.database import get_engine
from app.models.commission_log.entity import CommissionLog
from app.models.order.entity import Order
from app.models.stat.entity import Stat
from app.models.stat_server.entity import StatServer
from app.models.user.entity import User

async def aggregate_stats(ctx: dict, record_type: str, record_at: int) -> None:
    """聚合站点统计数据。

    这个任务对应原版 `V2boardStatistics::stat()` 背后的
    `StatisticalService::generateStatData()`。
    """
    start_at = int(record_at)
    end_at = _range_end(start_at, record_type)

    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        try:
            data = await _generate_stat_data(db, start_at, end_at)
            stmt = select(Stat).where(Stat.record_at == start_at)
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()
            if item is None:
                db.add(Stat(record_at=start_at, record_type=record_type, **data))
            else:
                item.record_type = record_type
                for key, value in data.items():
                    setattr(item, key, value)
            await db.flush()
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def _generate_stat_data(db: AsyncSession, start_at: int, end_at: int) -> dict:
    order_count = await _count(db, Order, Order.created_at >= start_at, Order.created_at < end_at)
    order_total = await _sum(db, Order.total_amount, Order.created_at >= start_at, Order.created_at < end_at)
    paid_filter = (
        Order.paid_at >= start_at,
        Order.paid_at < end_at,
        Order.status.notin_([0, 2]),  # type: ignore[attr-defined]
    )
    commission_filter = (
        CommissionLog.created_at >= start_at,
        CommissionLog.created_at < end_at,
    )
    register_filter = (
        User.created_at >= start_at,
        User.created_at < end_at,
    )
    transfer_filter = (
        StatServer.created_at >= start_at,
        StatServer.created_at < end_at,
    )
    return {
        "order_count": order_count,
        "order_total": order_total,
        "commission_count": await _count(db, CommissionLog, *commission_filter),
        "commission_total": await _sum(db, CommissionLog.get_amount, *commission_filter),
        "paid_count": await _count(db, Order, *paid_filter),
        "paid_total": await _sum(db, Order.total_amount, *paid_filter),
        "register_count": await _count(db, User, *register_filter),
        "invite_count": await _count(db, User, *register_filter, User.invite_user_id.is_not(None)),  # type: ignore[attr-defined]
        "transfer_used_total": str(
            await _sum(db, StatServer.u + StatServer.d, *transfer_filter)  # type: ignore[operator]
        ),
    }


async def _count(db: AsyncSession, model, *filters) -> int:
    stmt = select(func.count()).select_from(model).where(*filters)
    result = await db.execute(stmt)
    return int(result.scalar_one() or 0)


async def _sum(db: AsyncSession, column, *filters) -> int:
    stmt = select(func.coalesce(func.sum(column), 0)).where(*filters)
    result = await db.execute(stmt)
    return int(result.scalar_one() or 0)


def _range_end(start_at: int, record_type: str) -> int:
    current = time.localtime(start_at)
    if record_type == "m":
        days = monthrange(current.tm_year, current.tm_mon)[1]
        return start_at + days * 86400
    return start_at + 86400
