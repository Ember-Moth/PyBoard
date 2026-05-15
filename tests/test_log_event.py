"""统一日志事件测试。"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.log_event.entity import LogEvent
from app.services.log_event import cleanup_log_events_by_retention


async def test_api_request_writes_log_event_and_redacts_query(client, engine):
    response = await client.get("/api/v1/plans?token=secret-token&q=visible")
    assert response.status_code == 200
    assert response.headers["x-request-id"]

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        result = await db.execute(select(LogEvent).where(LogEvent.path == "/api/v1/plans"))
        event = result.scalar_one()

    assert event.category == "access"
    assert event.event == "http.request"
    assert event.status_code == 200
    assert event.data is not None
    assert event.data["query"]["token"] == "***"
    assert event.data["query"]["q"] == "visible"


async def test_admin_logs_api_returns_log_events(admin_client):
    await admin_client.get("/api/v1/plans")

    response = await admin_client.get("/api/v1/admin/logs?category=access&limit=10")
    assert response.status_code == 200
    logs = response.json()["data"]
    assert logs
    assert logs[0]["category"] == "access"
    assert "message" in logs[0]


async def test_log_retention_cleanup_skips_protected_categories(session):
    old = 1_700_000_000
    session.add_all(
        [
            LogEvent(
                category="access",
                level="info",
                event="http.request",
                message="old access",
                created_at=old,
                updated_at=old,
            ),
            LogEvent(
                category="commission",
                level="info",
                event="commission.granted",
                message="old commission",
                created_at=old,
                updated_at=old,
            ),
            LogEvent(
                category="audit",
                level="info",
                event="order.completed",
                message="old audit",
                created_at=old,
                updated_at=old,
            ),
        ]
    )
    await session.flush()

    deleted = await cleanup_log_events_by_retention(session, now=old + 365 * 86400)

    assert deleted["access"] == 1
    events = (await session.execute(select(LogEvent.event))).scalars().all()
    assert "http.request" not in events
    assert "commission.granted" in events
    assert "order.completed" in events
