"""订单 Repository —— 订单表专用查询。"""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.order.entity import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """订单专用查询方法。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Order)

    async def get_by_trade_no(self, trade_no: str) -> Order | None:
        """根据交易号查询订单。"""
        stmt = select(Order).where(Order.trade_no == trade_no)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_trade_no_for_update(self, trade_no: str) -> Order | None:
        """根据交易号锁定订单行，用于订单开通这类强一致流程。"""
        stmt = (
            select(Order)
            .where(Order.trade_no == trade_no)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, order_id: int) -> Order | None:
        """根据 ID 锁定订单行。"""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, user_id: int, status: int | None = None, offset: int = 0, limit: int = 50
    ) -> list[Order]:
        """查询用户订单，支持按状态筛选。"""
        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        if status is not None:
            stmt = stmt.where(Order.status == status)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def has_pending_order(self, user_id: int) -> bool:
        """检查用户是否有待支付订单。"""
        stmt = select(Order.id).where(Order.user_id == user_id).where(Order.status == 0).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_pending_by_trade_no(self, trade_no: str, user_id: int) -> Order | None:
        """获取用户待支付的指定订单。"""
        stmt = (
            select(Order)
            .where(Order.trade_no == trade_no)
            .where(Order.user_id == user_id)
            .where(Order.status == 0)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_paid_order(self, user_id: int) -> bool:
        """检查用户是否有已完成订单。"""
        stmt = select(Order.id).where(Order.user_id == user_id).where(Order.status.in_([3, 4])).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_completed_plan_orders(self, user_id: int) -> int:
        """统计用户已完成的套餐订单。"""
        stmt = (
            select(func.count())
            .select_from(Order)
            .where(Order.user_id == user_id)
            .where(Order.plan_id > 0)
            .where(Order.status == 3)
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def sum_pending_commission(self, invite_user_id: int) -> int:
        """统计邀请人待确认佣金。"""
        stmt = (
            select(func.coalesce(func.sum(Order.commission_balance), 0))
            .where(Order.status == 3)
            .where(Order.commission_status == 0)
            .where(Order.invite_user_id == invite_user_id)
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
