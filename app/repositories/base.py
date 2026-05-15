"""Repository 基类 —— 提供通用异步 CRUD。"""

from typing import Generic, TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """通用 Repository，子类只需传入 model 类型。"""

    def __init__(self, db: AsyncSession, model: type[ModelType]):
        self.db = db
        self.model = model

    # ---- 查询 ----
    async def get_all(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        """分页查询全部记录。"""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, id: int) -> ModelType | None:
        """根据主键查询单条记录。"""
        return await self.db.get(self.model, id)

    async def count(self) -> int:
        """返回记录总数。"""
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    # ---- 写操作 ----
    async def create(self, obj: ModelType) -> ModelType:
        """创建记录，时间戳由 PostgreSQL DEFAULT/触发器维护。"""
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        """更新记录，updated_at 由 PostgreSQL 触发器维护。"""
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        """删除记录。"""
        await self.db.delete(obj)
        await self.db.flush()
