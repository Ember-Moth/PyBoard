"""支付方式 Repository —— 支付方式表专用查询。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select

from app.models.order.entity import Order
from app.models.payment.entity import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """支付方式专用查询方法。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Payment)

    async def get_enabled_methods(self) -> list[Payment]:
        """获取所有启用的支付方式（按排序）。"""
        stmt = (
            select(Payment)
            .where(Payment.enable.is_(True))
            .order_by(Payment.sort.asc().nulls_last())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_enabled_by_id(self, payment_id: int) -> Payment | None:
        """获取启用的指定支付方式。"""
        stmt = (
            select(Payment)
            .where(Payment.id == payment_id)
            .where(Payment.enable.is_(True))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid: str) -> Payment | None:
        """根据支付方式 UUID 查询。"""
        stmt = select(Payment).where(Payment.uuid == uuid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_orders(self, payment_id: int) -> bool:
        """检查支付方式是否已被订单引用。"""
        stmt = select(func.count()).select_from(Order).where(Order.payment_id == payment_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one()) > 0
