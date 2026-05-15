"""工单消息 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.ticket_message.entity import TicketMessage
from app.repositories.base import BaseRepository


class TicketMessageRepository(BaseRepository[TicketMessage]):
    """工单消息专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, TicketMessage)

    async def list_by_ticket(self, ticket_id: int) -> list[TicketMessage]:
        stmt = select(TicketMessage).where(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.id.asc())  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_last_by_ticket(self, ticket_id: int) -> TicketMessage | None:
        stmt = select(TicketMessage).where(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.id.desc()).limit(1)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
