"""管理端统计和系统接口测试。"""

import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.order.entity import Order
from app.models.stat_server.entity import StatServer
from app.models.stat_user.entity import StatUser


async def _seed_stats(engine) -> None:
    now = int(time.time())
    today = now - (now % 86400)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(
            Order(
                user_id=1,
                plan_id=0,
                type=9,
                period="deposit",
                trade_no="STATAPI",
                total_amount=1000,
                status=3,
                paid_at=now,
                created_at=now,
            )
        )
        db.add(
            StatServer(
                server_id=1,
                server_type="vless",
                u=100,
                d=200,
                record_type="d",
                record_at=today,
                created_at=now,
            )
        )
        db.add(
            StatUser(
                user_id=1,
                server_rate=1,
                u=50,
                d=60,
                record_type="d",
                record_at=today,
                created_at=now,
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_admin_stats_and_system(admin_client, engine):
    await _seed_stats(engine)

    res = await admin_client.get("/api/v1/admin/stats/overview")
    assert res.status_code == 200
    assert res.json()["data"]["order_count"] == 1

    res = await admin_client.get("/api/v1/admin/stats/servers/rank")
    assert res.status_code == 200
    assert res.json()["data"][0]["total"] == 300

    res = await admin_client.get("/api/v1/admin/stats/users/rank")
    assert res.status_code == 200
    assert res.json()["data"][0]["total"] == 110

    res = await admin_client.get("/api/v1/admin/stats/users/1/traffic")
    assert res.status_code == 200
    assert res.json()["data"][0]["user_id"] == 1

    res = await admin_client.get("/api/v1/admin/system/status")
    assert res.status_code == 200
    assert "python" in res.json()["data"]

    res = await admin_client.get("/api/v1/admin/system/queues")
    assert res.status_code == 200
    assert "queues" in res.json()["data"]
