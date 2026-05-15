"""优惠券 Repository。"""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.coupon.entity import Coupon
from app.models.order.entity import Order
from app.repositories.base import BaseRepository


class CouponRepository(BaseRepository[Coupon]):
    """优惠券专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Coupon)

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[Coupon]:
        stmt = select(Coupon).order_by(Coupon.id.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Coupon | None:
        stmt = select(Coupon).where(Coupon.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, coupon_id: int) -> Coupon | None:
        stmt = select(Coupon).where(Coupon.id == coupon_id).with_for_update().execution_options(populate_existing=True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def code_exists(self, code: str) -> bool:
        return await self.get_by_code(code) is not None

    async def count_used(self, coupon_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Order)
            .where(Order.coupon_id == coupon_id)
            .where(Order.status.not_in([0, 2]))
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def count_user_used(self, coupon_id: int, user_id: int, exclude_order_id: int | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(Order)
            .where(Order.coupon_id == coupon_id)
            .where(Order.user_id == user_id)
            .where(Order.status.not_in([0, 2]))
        )
        if exclude_order_id is not None:
            stmt = stmt.where(Order.id != exclude_order_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
