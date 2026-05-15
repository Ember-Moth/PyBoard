"""Plan 仓储层 —— 套餐数据访问。"""

import time

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.plan.entity import Plan
from app.models.user.entity import User
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    """套餐专用 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Plan)

    async def list_visible(self) -> list[Plan]:
        """用户端列表 —— show=True，按 sort 升序。"""
        stmt = (
            select(Plan)
            .where(Plan.show == True)  # noqa: E712
            .order_by(
                Plan.sort.asc().nulls_last(),  # type: ignore[union-attr]
                Plan.id.asc(),  # type: ignore[union-attr]
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[Plan]:
        """管理端列表 —— 全量，按 sort 升序。"""
        stmt = select(Plan).order_by(
            Plan.sort.asc().nulls_last(),  # type: ignore[union-attr]
            Plan.id.asc(),  # type: ignore[union-attr]
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_for_update(self, plan_id: int) -> Plan | None:
        """锁定套餐行，用于容量校验与开通串行化。"""
        stmt = select(Plan).where(Plan.id == plan_id).with_for_update().execution_options(populate_existing=True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_active_users(self) -> dict[int, int]:
        """统计每个套餐的活跃用户数（过期时间未到 或 永久有效）。

        Returns: {plan_id: count}
        """
        now = int(time.time())
        stmt = (
            select(User.plan_id, func.count())
            .where(User.plan_id.is_not(None))
            .where(or_(User.expired_at >= now, User.expired_at.is_(None)))
            .group_by(User.plan_id)
        )
        result = await self.db.execute(stmt)
        return {plan_id: cnt for plan_id, cnt in result.all()}

    async def has_orders(self, plan_id: int) -> bool:
        """检查套餐下是否存在订单（用于删除校验）。"""
        from app.models.order.entity import Order

        stmt = select(func.count()).select_from(Order).where(Order.plan_id == plan_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one()) > 0

    async def has_active_users(self, plan_id: int) -> bool:
        """检查套餐下是否存在活跃用户（用于删除校验）。"""
        now = int(time.time())
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.plan_id == plan_id)
            .where(or_(User.expired_at >= now, User.expired_at.is_(None)))
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one()) > 0
