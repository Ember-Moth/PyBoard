"""服务器分组 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.server_group.entity import ServerGroup
from app.repositories.base import BaseRepository


class ServerGroupRepository(BaseRepository[ServerGroup]):
    """服务器分组专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, ServerGroup)

    async def list_all(self) -> list[ServerGroup]:
        stmt = select(ServerGroup).order_by(ServerGroup.id.asc())  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
