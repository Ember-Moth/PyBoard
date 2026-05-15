"""邀请码 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.invite_code.entity import InviteCode
from app.repositories.base import BaseRepository


class InviteCodeRepository(BaseRepository[InviteCode]):
    """邀请码专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, InviteCode)

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[InviteCode]:
        stmt = select(InviteCode).order_by(InviteCode.id.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int, status: int | None = None) -> list[InviteCode]:
        stmt = select(InviteCode).where(InviteCode.user_id == user_id).order_by(InviteCode.id.desc())  # type: ignore[union-attr]
        if status is not None:
            stmt = stmt.where(InviteCode.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_active_by_user(self, user_id: int) -> int:
        stmt = select(InviteCode).where(InviteCode.user_id == user_id).where(InviteCode.status == 0)
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_active_by_code(self, code: str) -> InviteCode | None:
        stmt = select(InviteCode).where(InviteCode.code == code).where(InviteCode.status == 0)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> InviteCode | None:
        stmt = select(InviteCode).where(InviteCode.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def code_exists(self, code: str) -> bool:
        stmt = select(InviteCode.id).where(InviteCode.code == code).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
