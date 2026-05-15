"""周期性维护任务测试。"""

import time

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

import app.core.database as database
from app.models.order.entity import Order
from app.models.user.entity import User
from app.queues.jobs import pg_cache
from app.queues.jobs.maintenance import aggregate_yesterday_stats, check_order, traffic_update
from app.queues.names import QUEUE_ORDER_HANDLE


def _bind_global_engine(monkeypatch, engine) -> None:
    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_session_factory", None)


@pytest.mark.asyncio
async def test_traffic_update_flushes_unlogged_traffic_to_users(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = User(
            email="traffic-update@test.local",
            password="hash",
            token="traffic-token",
            uuid="traffic-uuid",
            u=10,
            d=20,
        )
        db.add(user)
        await db.flush()
        user_id = int(user.id)
        await db.commit()

    async with factory() as db:
        await db.execute(
            text("INSERT INTO traffic_cache(stage, user_id, u, d) VALUES ('active', :user_id, 100, 200)"),
            {"user_id": user_id},
        )
        await db.commit()

    await traffic_update({})

    async with factory() as db:
        user = (await db.execute(select(User).where(User.email == "traffic-update@test.local"))).scalar_one()
        assert user.u == 110
        assert user.d == 220
        assert user.t > 0

    async with factory() as db:
        assert int((await db.execute(text("SELECT count(*) FROM traffic_cache"))).scalar_one()) == 0


@pytest.mark.asyncio
async def test_traffic_update_skips_when_reset_lock_exists(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = User(
            email="traffic-lock@test.local",
            password="hash",
            token="traffic-lock-token",
            uuid="traffic-lock-uuid",
        )
        db.add(user)
        await db.flush()
        user_id = int(user.id)
        await db.commit()

    async with factory() as db:
        await db.execute(text("INSERT INTO runtime_cache(key, value) VALUES ('traffic_reset_lock', 'true'::jsonb)"))
        await db.execute(
            text("INSERT INTO traffic_cache(stage, user_id, u, d) VALUES ('active', :user_id, 100, 0)"),
            {"user_id": user_id},
        )
        await db.commit()

    await traffic_update({})

    async with factory() as db:
        user = (await db.execute(select(User).where(User.email == "traffic-lock@test.local"))).scalar_one()
        assert user.u == 0
    async with factory() as db:
        cached = (
            await db.execute(text("SELECT u FROM traffic_cache WHERE stage = 'active' AND user_id = :user_id"), {"user_id": user_id})
        ).scalar_one()
        assert cached == 100


@pytest.mark.asyncio
async def test_traffic_update_rolls_back_cache_when_database_fails(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        await db.execute(text("INSERT INTO traffic_cache(stage, user_id, u, d) VALUES ('active', 1, 100, 200)"))
        await db.commit()

    async def fail_apply(db, rows):
        raise RuntimeError("database down")

    monkeypatch.setattr(pg_cache, "_apply_processing_traffic", fail_apply)
    with pytest.raises(RuntimeError, match="database down"):
        await traffic_update({})

    async with factory() as db:
        row = (
            await db.execute(text("SELECT stage, u, d FROM traffic_cache WHERE user_id = 1"))
        ).one()
        assert (row.stage, row.u, row.d) == ("active", 100, 200)


@pytest.mark.asyncio
async def test_traffic_update_processes_existing_staged_traffic_before_new_active(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = User(
            email="traffic-staged@test.local",
            password="hash",
            token="traffic-staged-token",
            uuid="traffic-staged-uuid",
        )
        db.add(user)
        await db.flush()
        user_id = int(user.id)
        await db.commit()

    async with factory() as db:
        await db.execute(
            text("INSERT INTO traffic_cache(stage, user_id, u, d) VALUES ('processing', :user_id, 100, 200)"),
            {"user_id": user_id},
        )
        await db.execute(
            text("INSERT INTO traffic_cache(stage, user_id, u, d) VALUES ('active', :user_id, 300, 400)"),
            {"user_id": user_id},
        )
        await db.commit()

    await traffic_update({})

    async with factory() as db:
        user = (await db.execute(select(User).where(User.email == "traffic-staged@test.local"))).scalar_one()
        assert user.u == 100
        assert user.d == 200

    async with factory() as db:
        row = (
            await db.execute(text("SELECT u, d FROM traffic_cache WHERE stage = 'active' AND user_id = :user_id"), {"user_id": user_id})
        ).one()
        assert (row.u, row.d) == (300, 400)


@pytest.mark.asyncio
async def test_check_order_enqueues_pending_and_paid_orders(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    now = int(time.time())
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add_all(
            [
                Order(
                    user_id=1,
                    plan_id=0,
                    type=9,
                    period="deposit",
                    trade_no="PENDING",
                    total_amount=100,
                    status=0,
                    created_at=now - 2,
                ),
                Order(
                    user_id=1,
                    plan_id=0,
                    type=9,
                    period="deposit",
                    trade_no="PAID",
                    total_amount=100,
                    status=1,
                    created_at=now - 1,
                ),
                Order(
                    user_id=1,
                    plan_id=0,
                    type=9,
                    period="deposit",
                    trade_no="DONE",
                    total_amount=100,
                    status=3,
                    created_at=now,
                ),
            ]
        )
        await db.commit()

    class FakeQueue:
        def __init__(self) -> None:
            self.jobs: list[tuple[str, tuple, dict]] = []

        async def enqueue_job(self, name: str, *args, **kwargs) -> None:
            self.jobs.append((name, args, kwargs))

    queue = FakeQueue()
    await check_order({"queue": queue})

    assert queue.jobs == [
        (
            "order_handle",
            ("PENDING",),
            {"_queue_name": QUEUE_ORDER_HANDLE, "_job_id": "order_handle:PENDING"},
        ),
        (
            "order_handle",
            ("PAID",),
            {"_queue_name": QUEUE_ORDER_HANDLE, "_job_id": "order_handle:PAID"},
        ),
    ]


@pytest.mark.asyncio
async def test_aggregate_yesterday_stats_delegates_to_stat_job(monkeypatch):
    calls = []

    async def fake_aggregate_stats(ctx, record_type, record_at):
        calls.append((ctx, record_type, record_at))

    monkeypatch.setattr("app.queues.jobs.maintenance.aggregate_stats", fake_aggregate_stats)
    await aggregate_yesterday_stats({"queue": "queue"})

    assert len(calls) == 1
    assert calls[0][0] == {"queue": "queue"}
    assert calls[0][1] == "d"
    assert calls[0][2] <= int(time.time()) - 86400
