"""PlanRepository 单元测试。"""

import secrets

import pytest

from app.models.plan.entity import Plan
from app.models.user.entity import User
from app.repositories.plan import PlanRepository
from app.repositories.user import UserRepository
from app.utils.password import hash_password


def _make_plan(name: str, *, show: bool = True, capacity_limit: int | None = None) -> Plan:
    return Plan(
        name=name,
        group_id=1,
        transfer_enable=10 * 1024**3,
        show=show,
        capacity_limit=capacity_limit,
    )


def _make_user(email: str, *, plan_id: int | None = None, expired_at: int | None = None) -> User:
    return User(
        email=email,
        password=hash_password("test"),
        token=secrets.token_hex(8),
        uuid=secrets.token_hex(12),
        plan_id=plan_id,
        expired_at=expired_at,
    )


@pytest.mark.asyncio
async def test_list_visible_filters_hidden(session):
    repo = PlanRepository(session)
    await repo.create(_make_plan("visible", show=True))
    await repo.create(_make_plan("hidden", show=False))

    items = await repo.list_visible()
    assert [p.name for p in items] == ["visible"]


@pytest.mark.asyncio
async def test_count_active_users(session):
    plan_repo = PlanRepository(session)
    user_repo = UserRepository(session)

    plan_a = await plan_repo.create(_make_plan("A"))
    plan_b = await plan_repo.create(_make_plan("B"))

    # plan_a 有 1 个活跃用户（未过期）
    await user_repo.create(_make_user("a@test.local", plan_id=plan_a.id, expired_at=9999999999))

    # plan_b 有 1 个活跃 + 1 个过期
    await user_repo.create(_make_user("b1@test.local", plan_id=plan_b.id, expired_at=9999999999))
    await user_repo.create(_make_user("b2@test.local", plan_id=plan_b.id, expired_at=0))

    # 无套餐用户不计入
    await user_repo.create(_make_user("none@test.local", plan_id=None))

    counts = await plan_repo.count_active_users()
    assert counts[plan_a.id] == 1  # type: ignore[index]
    assert counts[plan_b.id] == 1  # type: ignore[index]


@pytest.mark.asyncio
async def test_has_active_users(session):
    plan_repo = PlanRepository(session)
    user_repo = UserRepository(session)

    plan = await plan_repo.create(_make_plan("P"))

    # 无用户
    assert await plan_repo.has_active_users(plan.id) is False  # type: ignore[arg-type]

    # 有活跃用户
    await user_repo.create(_make_user("u@test.local", plan_id=plan.id, expired_at=9999999999))
    assert await plan_repo.has_active_users(plan.id) is True  # type: ignore[arg-type]


# 注：has_orders 逻辑在 Service delete 方法里通过异常抛出来
# 等 OrderRepository 建好了再补单测
