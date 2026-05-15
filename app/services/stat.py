"""统计查询服务。"""

import time
from typing import Any

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.order.entity import Order
from app.models.stat.entity import Stat
from app.models.stat_server.entity import StatServer
from app.models.stat_user.entity import StatUser


class StatService:
    """后台和用户端统计查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def overview(self) -> dict[str, Any]:
        latest = (await self.db.execute(select(Stat).order_by(Stat.record_at.desc()).limit(1))).scalar_one_or_none()
        if latest:
            return latest.model_dump()
        return {
            "order_count": await self._count(Order),
            "order_total": await self._sum(Order.total_amount),
            "paid_count": await self._count(Order, Order.status.notin_([0, 2])),  # type: ignore[attr-defined]
            "paid_total": await self._sum(Order.total_amount, Order.status.notin_([0, 2])),  # type: ignore[attr-defined]
            "commission_count": 0,
            "commission_total": 0,
            "register_count": 0,
            "invite_count": 0,
            "transfer_used_total": str(await self._sum(StatServer.u + StatServer.d)),  # type: ignore[operator]
        }

    async def order_series(self, limit: int = 30) -> list[dict[str, Any]]:
        stmt = select(Stat).order_by(Stat.record_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return [item.model_dump() for item in result.scalars().all()]

    async def server_rank(self, period: str = "today", limit: int = 15) -> list[dict[str, Any]]:
        start_at, end_at = _period_range(period)
        stmt = (
            select(
                StatServer.server_id,
                StatServer.server_type,
                func.coalesce(func.sum(StatServer.u), 0).label("u"),
                func.coalesce(func.sum(StatServer.d), 0).label("d"),
                (func.coalesce(func.sum(StatServer.u), 0) + func.coalesce(func.sum(StatServer.d), 0)).label("total"),
            )
            .where(StatServer.record_at >= start_at)
            .where(StatServer.record_at < end_at)
            .group_by(StatServer.server_id, StatServer.server_type)
            .order_by((func.coalesce(func.sum(StatServer.u), 0) + func.coalesce(func.sum(StatServer.d), 0)).desc())
            .limit(limit)
        )
        return [_normalize_rank_row(row._mapping) for row in (await self.db.execute(stmt)).all()]

    async def user_rank(self, period: str = "today", limit: int = 30) -> list[dict[str, Any]]:
        start_at, end_at = _period_range(period)
        stmt = (
            select(
                StatUser.user_id,
                StatUser.server_rate,
                func.coalesce(func.sum(StatUser.u), 0).label("u"),
                func.coalesce(func.sum(StatUser.d), 0).label("d"),
                (func.coalesce(func.sum(StatUser.u), 0) + func.coalesce(func.sum(StatUser.d), 0)).label("total"),
            )
            .where(StatUser.record_at >= start_at)
            .where(StatUser.record_at < end_at)
            .group_by(StatUser.user_id, StatUser.server_rate)
            .order_by((func.coalesce(func.sum(StatUser.u), 0) + func.coalesce(func.sum(StatUser.d), 0)).desc())
            .limit(limit)
        )
        return [_normalize_rank_row(row._mapping) for row in (await self.db.execute(stmt)).all()]

    async def user_traffic_log(self, user_id: int, limit: int = 30) -> list[dict[str, Any]]:
        stmt = (
            select(StatUser)
            .where(StatUser.user_id == user_id)
            .order_by(StatUser.record_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [item.model_dump() for item in result.scalars().all()]

    async def _count(self, model, *filters) -> int:
        result = await self.db.execute(select(func.count()).select_from(model).where(*filters))
        return int(result.scalar_one() or 0)

    async def _sum(self, column, *filters) -> int:
        result = await self.db.execute(select(func.coalesce(func.sum(column), 0)).where(*filters))
        return int(result.scalar_one() or 0)


def _period_range(period: str) -> tuple[int, int]:
    today = _today_timestamp()
    if period in {"last", "yesterday"}:
        return today - 86400, today
    if period == "all":
        return 0, 4_102_444_800
    return today, today + 86400


def _today_timestamp() -> int:
    now = int(time.time())
    return now - (now % 86400)


def _normalize_rank_row(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key in ("u", "d", "total"):
        data[key] = int(data.get(key) or 0)
    if "server_id" in data:
        data["server_id"] = int(data["server_id"])
    if "user_id" in data:
        data["user_id"] = int(data["user_id"])
    if "server_rate" in data:
        data["server_rate"] = float(data["server_rate"])
    return data
