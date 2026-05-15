"""测试公共 fixture。

设计目标：
- 隔离：每个测试用独立的 PostgreSQL schema，互不影响。
- 真实：通过依赖覆盖而非 mock，链路与生产一致。
- 简单：测试只需注入 `client` 或 `session`，其余自动装配。
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from sqlmodel import SQLModel

# 在导入应用前，先注册所有模型，确保 SQLModel.metadata 包含全部表
import app.models  # noqa: F401  # 触发模型注册
from app.core.cache import RuntimeCache
from app.core.config import settings
from app.core.database import get_db
from app.core.queue import get_queue
from main import app


# ---- 事件循环 ----
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# ---- 数据库 ----
@pytest_asyncio.fixture
async def engine():
    """每个测试一个独立 PostgreSQL schema。"""
    database_url = _test_database_url()
    if not database_url.startswith("postgresql+asyncpg://"):
        pytest.skip("测试需要 PostgreSQL 数据库，请配置 TEST_DATABASE_URL 或 PG_* 环境变量")

    schema = f"test_{uuid.uuid4().hex}"
    setup_engine = create_async_engine(database_url, poolclass=NullPool)
    async with setup_engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    await setup_engine.dispose()

    engine = create_async_engine(
        database_url,
        connect_args={"server_settings": {"search_path": schema}},
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(
            text(
                """
                CREATE UNLOGGED TABLE IF NOT EXISTS runtime_cache (
                    key text PRIMARY KEY,
                    value jsonb NOT NULL DEFAULT '{}'::jsonb,
                    expires_at bigint NULL,
                    created_at bigint NOT NULL DEFAULT (floor(extract(epoch from now())))::bigint,
                    updated_at bigint NOT NULL DEFAULT (floor(extract(epoch from now())))::bigint
                )
                """
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_runtime_cache_expires_at ON runtime_cache (expires_at)"))
        await conn.execute(
            text(
                """
                CREATE UNLOGGED TABLE IF NOT EXISTS traffic_cache (
                    stage text NOT NULL,
                    user_id bigint NOT NULL,
                    u bigint NOT NULL DEFAULT 0,
                    d bigint NOT NULL DEFAULT 0,
                    created_at bigint NOT NULL DEFAULT (floor(extract(epoch from now())))::bigint,
                    updated_at bigint NOT NULL DEFAULT (floor(extract(epoch from now())))::bigint,
                    PRIMARY KEY (stage, user_id)
                )
                """
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_traffic_cache_stage ON traffic_cache (stage)"))
        await conn.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION pyboard_set_epoch_timestamps()
                RETURNS trigger
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    epoch_now bigint := (floor(extract(epoch from now())))::bigint;
                BEGIN
                    IF TG_OP = 'INSERT' THEN
                        NEW.created_at := COALESCE(NULLIF(NEW.created_at, 0), epoch_now);
                        NEW.updated_at := COALESCE(NULLIF(NEW.updated_at, 0), NEW.created_at);
                    ELSE
                        NEW.updated_at := epoch_now;
                    END IF;
                    RETURN NEW;
                END;
                $$;
                """
            )
        )
        for table in SQLModel.metadata.sorted_tables:
            if "created_at" in table.c and "updated_at" in table.c:
                await conn.execute(text(f'DROP TRIGGER IF EXISTS trg_{table.name}_timestamps ON "{table.name}"'))
                await conn.execute(
                    text(
                        f"""
                        CREATE TRIGGER trg_{table.name}_timestamps
                        BEFORE INSERT OR UPDATE ON "{table.name}"
                        FOR EACH ROW EXECUTE FUNCTION pyboard_set_epoch_timestamps()
                        """
                    )
                )
        for table_name in ("runtime_cache", "traffic_cache"):
            await conn.execute(text(f"DROP TRIGGER IF EXISTS trg_{table_name}_timestamps ON {table_name}"))
            await conn.execute(
                text(
                    f"""
                    CREATE TRIGGER trg_{table_name}_timestamps
                    BEFORE INSERT OR UPDATE ON {table_name}
                    FOR EACH ROW EXECUTE FUNCTION pyboard_set_epoch_timestamps()
                    """
                )
            )

    try:
        yield engine
    finally:
        await engine.dispose()
        cleanup_engine = create_async_engine(database_url, poolclass=NullPool)
        async with cleanup_engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await cleanup_engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """函数级数据库会话，测试结束自动回滚。"""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


# ---- Runtime cache ----
@pytest_asyncio.fixture
async def cache(engine) -> AsyncGenerator[RuntimeCache, None]:
    """每个测试 schema 内的 PostgreSQL runtime cache。"""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        yield RuntimeCache(db)


# ---- HTTP 客户端 ----
@pytest_asyncio.fixture
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    """注入测试 DB 的 AsyncClient。"""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as db:
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def override_get_queue():
        return _TestQueue()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_queue] = override_get_queue

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---- 已认证客户端 ----
async def _register_and_get_token(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["auth_token"]


@pytest_asyncio.fixture
async def authed_client(client, engine) -> AsyncGenerator[AsyncClient, None]:
    """已注册并登录的普通用户客户端，Authorization 头已设置。"""
    token = await _register_and_get_token(client, "user@test.local")
    client.headers["Authorization"] = token
    yield client


@pytest_asyncio.fixture
async def admin_client(client, engine) -> AsyncGenerator[AsyncClient, None]:
    """已注册并提升为 admin 的客户端，Authorization 头已设置。"""
    token = await _register_and_get_token(client, "admin@test.local")

    # 直接改 DB 把用户提为 admin（绕过缺失的 admin 创建接口）
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.repositories.user import UserRepository

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = UserRepository(db)
        user = await repo.get_by_email("admin@test.local")
        assert user is not None
        user.is_admin = True
        await repo.update(user)
        await db.commit()

    client.headers["Authorization"] = token
    yield client


def _test_database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL") or settings.database_url


class _TestQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple, dict]] = []

    async def enqueue_job(self, name: str, *args, **kwargs) -> int:
        self.jobs.append((name, args, kwargs))
        return len(self.jobs)
