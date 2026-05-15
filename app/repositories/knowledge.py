"""Knowledge 仓储层 —— 知识库数据访问。"""

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.knowledge.entity import Knowledge
from app.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[Knowledge]):
    """知识库专用 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Knowledge)

    async def list_visible(
        self,
        *,
        language: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
    ) -> list[Knowledge]:
        """用户端列表 —— show=True，按 sort 升序，可选语言/分类/关键词过滤。

        关键词同时匹配 title 与 body。无分页（老项目按 category 分组返回全量）。
        """
        stmt = select(Knowledge).where(Knowledge.show == True)  # noqa: E712
        if language is not None:
            stmt = stmt.where(Knowledge.language == language)
        if category is not None:
            stmt = stmt.where(Knowledge.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(Knowledge.title.like(pattern), Knowledge.body.like(pattern))  # type: ignore[union-attr]
            )
        stmt = stmt.order_by(
            Knowledge.sort.asc().nulls_last(),  # type: ignore[union-attr]
            Knowledge.id.asc(),  # type: ignore[union-attr]
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, offset: int = 0, limit: int = 20) -> list[Knowledge]:
        """管理端列表 —— 全量，按 sort 升序。"""
        stmt = (
            select(Knowledge)
            .order_by(
                Knowledge.sort.asc().nulls_last(),  # type: ignore[union-attr]
                Knowledge.id.desc(),  # type: ignore[union-attr]
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_visible(self, knowledge_id: int) -> Knowledge | None:
        """获取已上线的单条记录（用户端用）。"""
        stmt = select(Knowledge).where(
            Knowledge.id == knowledge_id,
            Knowledge.show == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_languages(self) -> list[str]:
        """已上线知识涉及的语言列表（去重）。"""
        stmt = (
            select(Knowledge.language)
            .where(Knowledge.show == True)  # noqa: E712
            .distinct()
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def count_for_language(self, language: str | None = None) -> int:
        """统计已上线知识数量。"""
        stmt = (
            select(func.count())
            .select_from(Knowledge)
            .where(Knowledge.show == True)  # noqa: E712
        )
        if language is not None:
            stmt = stmt.where(Knowledge.language == language)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
