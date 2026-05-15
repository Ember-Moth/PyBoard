"""Notice 仓储层 —— 公告数据访问。"""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.notice.entity import Notice
from app.repositories.base import BaseRepository


class NoticeRepository(BaseRepository[Notice]):
    """公告专用 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Notice)

    async def list_visible(
        self,
        offset: int = 0,
        limit: int = 10,
    ) -> list[Notice]:
        """查询已上线公告（show=True），按创建时间倒序。"""
        stmt = (
            select(Notice)
            .where(Notice.show == True)  # noqa: E712
            .order_by(Notice.created_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_visible(self) -> int:
        """统计已上线公告数量。"""
        stmt = (
            select(func.count())
            .select_from(Notice)
            .where(Notice.show == True)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Notice]:
        """管理端列表 —— 不过滤 show，按 id 倒序。"""
        stmt = (
            select(Notice)
            .order_by(Notice.id.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
