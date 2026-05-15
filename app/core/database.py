"""数据库引擎全局单例 —— 一次创建、全局复用连接池。"""

import asyncio
from collections.abc import AsyncGenerator

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.migrations.seeds import seed_default_settings, seed_initial_admin

_engine: AsyncEngine | None = None
_session_factory: sessionmaker | None = None  # type: ignore[valid-type]


def get_engine() -> AsyncEngine:
    """惰性初始化引擎（全局单例），自动管理内置连接池。"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
    return _engine


def get_session_factory() -> sessionmaker:  # type: ignore[valid-type]
    """获取 session 工厂（全局单例）。"""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(  # type: ignore[call-overload]
            get_engine(),  # type: ignore[arg-type]
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def init_db() -> None:
    """应用启动时自动执行数据库迁移到最新版本，并补齐默认 seed。"""
    alembic_cfg = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    await seed_default_settings(get_engine())
    await seed_initial_admin(get_engine())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：从全局连接池获取数据库连接，请求结束自动归还。"""
    factory = get_session_factory()
    async with factory() as db:  # type: ignore[operator]
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def close_db() -> None:
    """应用关闭时释放引擎。"""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
