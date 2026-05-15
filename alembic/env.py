"""Alembic 迁移环境 —— 异步引擎 + 自动发现模型。"""

import asyncio
import os
import sys

# 确保项目根目录在 sys.path 中（alembic CLI 从项目根运行）
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

# ---- 自动导入所有模型（确保 SQLModel.metadata 包含全部表） ----
import app.models  # noqa: E402, F401

# ---- Alembic Config ----
config = context.config

# ---- 目标元数据 ----
target_metadata = SQLModel.metadata


def get_url() -> str:
    """从项目配置获取数据库 URL。"""
    return settings.database_url


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本（不连接数据库）。"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """在给定连接上执行迁移。"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在线模式：连接数据库并执行迁移。"""
    url = get_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,  # 迁移时不复用连接池
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
