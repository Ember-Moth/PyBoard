"""礼品卡 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.giftcard.entity import Giftcard
from app.repositories.base import BaseRepository


class GiftcardRepository(BaseRepository[Giftcard]):
    """礼品卡专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Giftcard)

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[Giftcard]:
        stmt = select(Giftcard).order_by(Giftcard.id.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Giftcard | None:
        stmt = select(Giftcard).where(Giftcard.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code_for_update(self, code: str) -> Giftcard | None:
        stmt = select(Giftcard).where(Giftcard.code == code).with_for_update().execution_options(populate_existing=True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def code_exists(self, code: str) -> bool:
        return await self.get_by_code(code) is not None
