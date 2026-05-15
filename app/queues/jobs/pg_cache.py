"""PostgreSQL UNLOGGED cache helpers used by queue jobs."""

import time
from decimal import Decimal
from typing import Any

import orjson
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_TRAFFIC_ACTIVE_STAGE = "active"
_TRAFFIC_PROCESSING_STAGE = "processing"
_TRAFFIC_UPDATE_LOCK_KEY = 9_203_202_601


async def cache_exists(db: AsyncSession, key: str) -> bool:
    now = int(time.time())
    result = await db.execute(
        text(
            """
            SELECT 1
            FROM runtime_cache
            WHERE key = :key
              AND (expires_at IS NULL OR expires_at > :now)
            LIMIT 1
            """
        ),
        {"key": key, "now": now},
    )
    return result.scalar_one_or_none() is not None


async def cache_set(db: AsyncSession, key: str, value: Any = True, ttl: int | None = None) -> None:
    now = int(time.time())
    expires_at = now + ttl if ttl else None
    await db.execute(
        text(
            """
            INSERT INTO runtime_cache(key, value, expires_at)
            VALUES (:key, CAST(:value AS jsonb), :expires_at)
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value,
                expires_at = EXCLUDED.expires_at
            """
        ),
        {"key": key, "value": orjson.dumps(value).decode(), "expires_at": expires_at},
    )


async def cache_delete(db: AsyncSession, key: str) -> None:
    await db.execute(text("DELETE FROM runtime_cache WHERE key = :key"), {"key": key})


async def increment_traffic_cache(db: AsyncSession, traffic: dict[int, tuple[int, int]], rate: Decimal) -> None:
    rows = [
        {
            "user_id": user_id,
            "u": int(Decimal(upload) * rate),
            "d": int(Decimal(download) * rate),
        }
        for user_id, (upload, download) in traffic.items()
    ]
    if not rows:
        return
    await db.execute(
        text(
            """
            INSERT INTO traffic_cache(stage, user_id, u, d)
            SELECT :stage, item.user_id, item.u, item.d
            FROM jsonb_to_recordset(CAST(:rows AS jsonb)) AS item(user_id bigint, u bigint, d bigint)
            ON CONFLICT (stage, user_id) DO UPDATE
            SET u = traffic_cache.u + EXCLUDED.u,
                d = traffic_cache.d + EXCLUDED.d
            """
        ),
        {"stage": _TRAFFIC_ACTIVE_STAGE, "rows": orjson.dumps(rows).decode()},
    )


async def flush_traffic_cache_to_users(db: AsyncSession) -> bool:
    """Flush cached traffic to users atomically.

    Returns False when another worker is already flushing or reset lock is present.
    """
    locked = await db.execute(text("SELECT pg_try_advisory_xact_lock(:lock_key)"), {"lock_key": _TRAFFIC_UPDATE_LOCK_KEY})
    if not locked.scalar():
        return False
    if await cache_exists(db, "traffic_reset_lock"):
        return False

    processing_count = await db.execute(
        text("SELECT count(*) FROM traffic_cache WHERE stage = :stage"),
        {"stage": _TRAFFIC_PROCESSING_STAGE},
    )
    if int(processing_count.scalar_one() or 0) == 0:
        await db.execute(
            text("UPDATE traffic_cache SET stage = :processing WHERE stage = :active"),
            {"processing": _TRAFFIC_PROCESSING_STAGE, "active": _TRAFFIC_ACTIVE_STAGE},
        )

    result = await db.execute(
        text(
            """
            SELECT user_id, u, d
            FROM traffic_cache
            WHERE stage = :stage
            ORDER BY user_id
            """
        ),
        {"stage": _TRAFFIC_PROCESSING_STAGE},
    )
    rows = [dict(row._mapping) for row in result.all()]
    if not rows:
        return True

    await _apply_processing_traffic(db, rows)
    await db.execute(text("DELETE FROM traffic_cache WHERE stage = :stage"), {"stage": _TRAFFIC_PROCESSING_STAGE})
    return True


async def _apply_processing_traffic(db: AsyncSession, rows: list[dict[str, Any]]) -> None:
    now = int(time.time())
    payload = [
        {
            "user_id": int(row["user_id"]),
            "u": int(row["u"] or 0),
            "d": int(row["d"] or 0),
        }
        for row in rows
    ]
    await db.execute(
        text(
            """
            WITH traffic AS (
                SELECT *
                FROM jsonb_to_recordset(CAST(:rows AS jsonb)) AS item(user_id bigint, u bigint, d bigint)
            )
            UPDATE users AS users
            SET u = users.u + traffic.u,
                d = users.d + traffic.d,
                t = :now
            FROM traffic
            WHERE users.id = traffic.user_id
            """
        ),
        {"rows": orjson.dumps(payload).decode(), "now": now},
    )
