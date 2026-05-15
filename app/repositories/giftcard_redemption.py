"""礼品卡兑换记录 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.giftcard_redemption.entity import GiftcardRedemption
from app.repositories.base import BaseRepository


class GiftcardRedemptionRepository(BaseRepository[GiftcardRedemption]):
    """礼品卡兑换记录专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, GiftcardRedemption)

    async def get_by_giftcard_and_user(self, giftcard_id: int, user_id: int) -> GiftcardRedemption | None:
        stmt = (
            select(GiftcardRedemption)
            .where(GiftcardRedemption.giftcard_id == giftcard_id)
            .where(GiftcardRedemption.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
