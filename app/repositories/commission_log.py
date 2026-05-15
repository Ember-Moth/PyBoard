"""佣金记录 Repository。"""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.commission_log.entity import CommissionLog
from app.repositories.base import BaseRepository


class CommissionLogRepository(BaseRepository[CommissionLog]):
    """佣金记录专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, CommissionLog)

    async def list_by_invite_user(self, user_id: int, offset: int = 0, limit: int = 50) -> list[CommissionLog]:
        stmt = (
            select(CommissionLog)
            .where(CommissionLog.invite_user_id == user_id)
            .order_by(CommissionLog.created_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[CommissionLog]:
        stmt = select(CommissionLog).order_by(CommissionLog.created_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_trade_no(self, trade_no: str) -> CommissionLog | None:
        stmt = select(CommissionLog).where(CommissionLog.trade_no == trade_no)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def sum_by_invite_user(self, user_id: int) -> int:
        stmt = select(func.coalesce(func.sum(CommissionLog.get_amount), 0)).where(CommissionLog.invite_user_id == user_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
