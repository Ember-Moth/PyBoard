"""Setting 仓储层。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.setting.entity import Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    """配置专用 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Setting)

    async def get_by_key(self, key: str) -> Setting | None:
        """根据配置键查询。"""
        stmt = select(Setting).where(Setting.key == key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
