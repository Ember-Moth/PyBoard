"""工单 Repository。"""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.ticket.entity import Ticket
from app.models.user.entity import User
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    """工单专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Ticket)

    async def list_by_user(self, user_id: int, offset: int = 0, limit: int = 50) -> list[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.updated_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_open_by_user(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(Ticket).where(Ticket.user_id == user_id).where(Ticket.status == 0)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 50,
        *,
        status: int | None = None,
        reply_status: int | None = None,
        email: str | None = None,
    ) -> list[Ticket]:
        stmt = select(Ticket)
        if status is not None:
            stmt = stmt.where(Ticket.status == status)
        if reply_status is not None:
            stmt = stmt.where(Ticket.reply_status == reply_status)
        if email:
            stmt = stmt.join(User, User.id == Ticket.user_id).where(User.email == email)
        stmt = stmt.order_by(Ticket.updated_at.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        *,
        status: int | None = None,
        reply_status: int | None = None,
        email: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Ticket)
        if status is not None:
            stmt = stmt.where(Ticket.status == status)
        if reply_status is not None:
            stmt = stmt.where(Ticket.reply_status == reply_status)
        if email:
            stmt = stmt.join(User, User.id == Ticket.user_id).where(User.email == email)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
