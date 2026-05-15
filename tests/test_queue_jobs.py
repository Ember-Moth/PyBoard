"""队列任务测试。"""

import time

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

import app.core.database as database
from app.models.commission_log.entity import CommissionLog
from app.models.failed_job.entity import FailedJob
from app.models.order.entity import Order
from app.models.queue_job.entity import QueueJob
from app.models.stat.entity import Stat
from app.models.stat_server.entity import StatServer
from app.models.stat_user.entity import StatUser
from app.models.user.entity import User
from app.repositories.failed_job import FailedJobRepository
from app.queues.jobs.order import order_handle
from app.queues.jobs.stat import aggregate_stats
from app.queues.jobs.traffic import stat_server, stat_user, traffic_fetch
from app.queues.names import QUEUE_ORDER_HANDLE
from app.core.queue import PostgresQueue
from app.services.admin_tools import FailedJobService


def _bind_global_engine(monkeypatch, engine) -> None:
    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_session_factory", None)


@pytest.mark.asyncio
async def test_traffic_queue_jobs_update_unlogged_cache_and_stats(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    data = {
        "1": [100, 200],
        "2": {"u": 10, "d": 20},
        "bad": [999, 999],
    }
    server = {"id": 7, "rate": "2"}
    await traffic_fetch({}, data, server, "vless")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        rows = (
            await db.execute(text("SELECT user_id, u, d FROM traffic_cache WHERE stage = 'active' ORDER BY user_id"))
        ).all()
        assert [(row.user_id, row.u, row.d) for row in rows] == [(1, 200, 400), (2, 20, 40)]

    await stat_user({}, data, server, "vless")
    await stat_server({}, data, server, "vless")

    async with factory() as db:
        users = (await db.execute(select(StatUser).order_by(StatUser.user_id))).scalars().all()
        assert [(item.user_id, item.server_rate, item.u, item.d) for item in users] == [
            (1, 2.0, 100, 200),
            (2, 2.0, 10, 20),
        ]

        server_stat = (await db.execute(select(StatServer))).scalar_one()
        assert server_stat.server_id == 7
        assert server_stat.server_type == "vless"
        assert server_stat.u == 110
        assert server_stat.d == 220


@pytest.mark.asyncio
async def test_postgres_queue_enqueue_deduplicates_job_key(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)
    queue = PostgresQueue()

    first_id = await queue.enqueue_job("order_handle", "TRADE", _queue_name=QUEUE_ORDER_HANDLE, _job_id="order:TRADE")
    second_id = await queue.enqueue_job("order_handle", "TRADE", _queue_name=QUEUE_ORDER_HANDLE, _job_id="order:TRADE")

    assert first_id is not None
    assert second_id is None

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        jobs = (await db.execute(select(QueueJob))).scalars().all()
        assert len(jobs) == 1
        assert jobs[0].queue == QUEUE_ORDER_HANDLE
        assert jobs[0].job_name == "order_handle"
        assert jobs[0].args == ["TRADE"]


@pytest.mark.asyncio
async def test_order_handle_cancels_old_pending_and_opens_paid_deposit(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    now = int(time.time())
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = User(
            email="queue@test.local",
            password="hash",
            token="queue-token",
            uuid="queue-uuid",
        )
        db.add(user)
        await db.flush()
        old = Order(
            user_id=user.id,
            plan_id=0,
            type=9,
            period="deposit",
            trade_no="OLD",
            total_amount=100,
            status=0,
            created_at=now - 7201,
            updated_at=now - 7201,
        )
        paid = Order(
            user_id=user.id,
            plan_id=0,
            type=9,
            period="deposit",
            trade_no="PAID",
            total_amount=500,
            status=1,
            created_at=now,
            updated_at=now,
        )
        db.add_all([old, paid])
        await db.commit()

    await order_handle({}, "OLD")
    await order_handle({}, "PAID")
    await order_handle({}, "PAID")

    async with factory() as db:
        old = (await db.execute(select(Order).where(Order.trade_no == "OLD"))).scalar_one()
        paid = (await db.execute(select(Order).where(Order.trade_no == "PAID"))).scalar_one()
        user = (await db.execute(select(User).where(User.email == "queue@test.local"))).scalar_one()
        assert old.status == 2
        assert paid.status == 3
        assert user.balance == 500


@pytest.mark.asyncio
async def test_failed_job_retry_keeps_original_queue(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = FailedJobRepository(db)
        failed = await repo.create(
            FailedJob(
                connection="postgresql",
                queue=QUEUE_ORDER_HANDLE,
                payload='{"job_name":"order_handle","args":["TRADE"],"kwargs":{}}',
                exception="boom",
                failed_at="2026-05-15 00:00:00",
            )
        )
        await db.commit()
        failed_id = int(failed.id)

    class FakeQueue:
        def __init__(self) -> None:
            self.jobs: list[tuple[str, tuple, dict]] = []

        async def enqueue_job(self, name: str, *args, **kwargs) -> None:
            self.jobs.append((name, args, kwargs))

    queue = FakeQueue()
    async with factory() as db:
        service = FailedJobService(FailedJobRepository(db))
        assert await service.retry_job(failed_id, queue) is True
        await db.commit()

    assert queue.jobs == [("order_handle", ("TRADE",), {"_queue_name": QUEUE_ORDER_HANDLE})]


@pytest.mark.asyncio
async def test_aggregate_stats_builds_stat_record(engine, monkeypatch):
    _bind_global_engine(monkeypatch, engine)

    start_at = int(time.time()) - 3600
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(
            Order(
                user_id=1,
                plan_id=0,
                type=9,
                period="deposit",
                trade_no="STAT",
                total_amount=1000,
                status=3,
                paid_at=start_at + 10,
                created_at=start_at + 10,
            )
        )
        db.add(
            CommissionLog(
                invite_user_id=1,
                user_id=2,
                trade_no="STAT",
                order_amount=1000,
                get_amount=100,
                created_at=start_at + 10,
            )
        )
        db.add(
            User(
                email="stat@test.local",
                password="hash",
                token="stat-token",
                uuid="stat-uuid",
                invite_user_id=1,
                created_at=start_at + 10,
            )
        )
        db.add(
            StatServer(
                server_id=1,
                server_type="vless",
                u=20,
                d=30,
                record_type="d",
                record_at=start_at,
                created_at=start_at + 10,
            )
        )
        await db.commit()

    await aggregate_stats({}, "d", start_at)

    async with factory() as db:
        stat = (await db.execute(select(Stat).where(Stat.record_at == start_at))).scalar_one()
        assert stat.order_count == 1
        assert stat.order_total == 1000
        assert stat.paid_count == 1
        assert stat.paid_total == 1000
        assert stat.commission_count == 1
        assert stat.commission_total == 100
        assert stat.register_count == 1
        assert stat.invite_count == 1
        assert stat.transfer_used_total == "50"
