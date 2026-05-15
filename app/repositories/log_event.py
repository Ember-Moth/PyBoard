"""统一日志事件 Repository。"""

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.log_event.entity import LogEvent
from app.repositories.base import BaseRepository


class LogEventRepository(BaseRepository[LogEvent]):
    """日志事件专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, LogEvent)

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 50,
        *,
        category: str | None = None,
        level: str | None = None,
        event: str | None = None,
        request_id: str | None = None,
        actor_id: int | None = None,
        ip: str | None = None,
        q: str | None = None,
    ) -> list[LogEvent]:
        stmt = select(LogEvent)
        if category:
            stmt = stmt.where(LogEvent.category == category)
        if level:
            stmt = stmt.where(LogEvent.level == level)
        if event:
            stmt = stmt.where(LogEvent.event == event)
        if request_id:
            stmt = stmt.where(LogEvent.request_id == request_id)
        if actor_id is not None:
            stmt = stmt.where(LogEvent.actor_id == actor_id)
        if ip:
            stmt = stmt.where(LogEvent.ip == ip)
        if q:
            keyword = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    LogEvent.message.ilike(keyword),  # type: ignore[attr-defined]
                    LogEvent.path.ilike(keyword),  # type: ignore[attr-defined]
                    LogEvent.event.ilike(keyword),  # type: ignore[attr-defined]
                    LogEvent.request_id.ilike(keyword),  # type: ignore[attr-defined]
                )
            )
        stmt = stmt.order_by(LogEvent.created_at.desc(), LogEvent.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
