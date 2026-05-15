"""失败任务 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.failed_job.entity import FailedJob
from app.repositories.base import BaseRepository


class FailedJobRepository(BaseRepository[FailedJob]):
    """失败任务专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, FailedJob)

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[FailedJob]:
        stmt = select(FailedJob).order_by(FailedJob.id.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
