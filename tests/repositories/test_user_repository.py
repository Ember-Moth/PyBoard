"""UserRepository 单元测试样例 —— 直接基于 session fixture。"""

import pytest

from app.repositories.user import UserRepository
from tests.factories import make_user


@pytest.mark.asyncio
async def test_create_sets_timestamps(session):
    repo = UserRepository(session)
    user = await repo.create(make_user(email="t1@test.local"))

    assert user.id is not None
    assert user.created_at > 0
    assert user.updated_at > 0


@pytest.mark.asyncio
async def test_get_by_email(session):
    repo = UserRepository(session)
    await repo.create(make_user(email="t2@test.local"))

    found = await repo.get_by_email("t2@test.local")
    missing = await repo.get_by_email("nope@test.local")

    assert found is not None
    assert found.email == "t2@test.local"
    assert missing is None


@pytest.mark.asyncio
async def test_email_exists(session):
    repo = UserRepository(session)
    await repo.create(make_user(email="t3@test.local"))

    assert await repo.email_exists("t3@test.local") is True
    assert await repo.email_exists("absent@test.local") is False
