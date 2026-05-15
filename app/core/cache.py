"""PostgreSQL UNLOGGED runtime cache.

It stores short-lived, discardable state such as verification codes,
one-time tokens, online state and rate counters.
"""

import time
from typing import Any

import orjson
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


class RuntimeCache:
    """Small async cache API backed by ``runtime_cache``."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str) -> Any | None:
        now = int(time.time())
        result = await self.db.execute(
            text(
                """
                SELECT value
                FROM runtime_cache
                WHERE key = :key
                  AND (expires_at IS NULL OR expires_at > :now)
                LIMIT 1
                """
            ),
            {"key": key, "now": now},
        )
        value = result.scalar_one_or_none()
        if value is None:
            await self._delete_expired_key(key, now)
        return _decode_jsonb(value)

    async def mget(self, keys: list[str]) -> list[Any | None]:
        if not keys:
            return []
        now = int(time.time())
        result = await self.db.execute(
            text(
                """
                WITH requested AS (
                    SELECT value AS key, ord
                    FROM jsonb_array_elements_text(CAST(:keys AS jsonb)) WITH ORDINALITY AS item(value, ord)
                )
                SELECT cache.value
                FROM requested
                LEFT JOIN runtime_cache AS cache
                  ON cache.key = requested.key
                 AND (cache.expires_at IS NULL OR cache.expires_at > :now)
                ORDER BY requested.ord
                """
            ),
            {"keys": orjson.dumps(keys).decode(), "now": now},
        )
        return [_decode_jsonb(row[0]) for row in result.all()]

    async def set(self, key: str, value: Any, ex: int | None = None, nx: bool = False) -> bool:
        now = int(time.time())
        expires_at = now + ex if ex else None
        payload = _encode_jsonb(value)
        if nx:
            await self._delete_expired_key(key, now)
            result = await self.db.execute(
                text(
                    """
                    INSERT INTO runtime_cache(key, value, expires_at)
                    VALUES (:key, CAST(:value AS jsonb), :expires_at)
                    ON CONFLICT (key) DO NOTHING
                    RETURNING 1
                    """
                ),
                {"key": key, "value": payload, "expires_at": expires_at},
            )
            return result.scalar_one_or_none() is not None

        await self.db.execute(
            text(
                """
                INSERT INTO runtime_cache(key, value, expires_at)
                VALUES (:key, CAST(:value AS jsonb), :expires_at)
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value,
                    expires_at = EXCLUDED.expires_at
                """
            ),
            {"key": key, "value": payload, "expires_at": expires_at},
        )
        return True

    async def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        result = await self.db.execute(
            text(
                """
                DELETE FROM runtime_cache
                WHERE key IN (
                    SELECT value
                    FROM jsonb_array_elements_text(CAST(:keys AS jsonb))
                )
                RETURNING key
                """
            ),
            {"keys": orjson.dumps(list(keys)).decode()},
        )
        return len(result.all())

    async def incr(self, key: str, ex: int | None = None) -> int:
        now = int(time.time())
        expires_at = now + ex if ex else None
        result = await self.db.execute(
            text(
                """
                INSERT INTO runtime_cache(key, value, expires_at)
                VALUES (:key, '1'::jsonb, :expires_at)
                ON CONFLICT (key) DO UPDATE
                SET value = CASE
                        WHEN runtime_cache.expires_at IS NOT NULL
                         AND runtime_cache.expires_at <= :now THEN '1'::jsonb
                        ELSE to_jsonb(
                            CASE
                                WHEN (runtime_cache.value #>> '{}') ~ '^-?[0-9]+$'
                                THEN (runtime_cache.value #>> '{}')::bigint
                                ELSE 0
                            END + 1
                        )
                    END,
                    expires_at = CASE
                        WHEN runtime_cache.expires_at IS NOT NULL
                         AND runtime_cache.expires_at <= :now THEN EXCLUDED.expires_at
                        WHEN runtime_cache.expires_at IS NULL
                         AND EXCLUDED.expires_at IS NOT NULL THEN EXCLUDED.expires_at
                        ELSE runtime_cache.expires_at
                    END
                RETURNING (value #>> '{}')::bigint
                """
            ),
            {"key": key, "expires_at": expires_at, "now": now},
        )
        return int(result.scalar_one())

    async def expire(self, key: str, ex: int) -> bool:
        result = await self.db.execute(
            text(
                """
                UPDATE runtime_cache
                SET expires_at = :expires_at
                WHERE key = :key
                RETURNING 1
                """
            ),
            {"key": key, "expires_at": int(time.time()) + ex},
        )
        return result.scalar_one_or_none() is not None

    async def cleanup_expired(self) -> int:
        result = await self.db.execute(
            text("DELETE FROM runtime_cache WHERE expires_at IS NOT NULL AND expires_at <= :now RETURNING key"),
            {"now": int(time.time())},
        )
        return len(result.all())

    async def _delete_expired_key(self, key: str, now: int) -> None:
        await self.db.execute(
            text("DELETE FROM runtime_cache WHERE key = :key AND expires_at IS NOT NULL AND expires_at <= :now"),
            {"key": key, "now": now},
        )


def get_cache(db: AsyncSession = Depends(get_db)) -> RuntimeCache:
    return RuntimeCache(db)


def _encode_jsonb(value: Any) -> str:
    if isinstance(value, bytes):
        value = value.decode()
    return orjson.dumps(value).decode()


def _decode_jsonb(value: Any) -> Any:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return orjson.loads(value)
    return value
