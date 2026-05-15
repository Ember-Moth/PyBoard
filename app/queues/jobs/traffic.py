"""节点流量与统计队列任务，对齐原版 TrafficFetch/StatUser/StatServer Job。"""

import time
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.core.database import get_engine
from app.models.stat_server.entity import StatServer
from app.models.stat_user.entity import StatUser
from app.queues.jobs.pg_cache import increment_traffic_cache


async def traffic_fetch(ctx: dict, data: dict[str, Any], server: dict[str, Any], protocol: str) -> None:
    """累计用户实时流量到 PostgreSQL UNLOGGED cache。

    原版写入外部内存缓存；当前项目改为写入 traffic_cache。
    """
    traffic = _normalize_traffic_data(data)
    if not traffic:
        return
    rate = _decimal_rate(server.get("rate", 1))
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        async with db.begin():
            await increment_traffic_cache(db, traffic, rate)


async def stat_user(
    ctx: dict,
    data: dict[str, Any],
    server: dict[str, Any],
    protocol: str,
    record_type: str = "d",
) -> None:
    """累计用户维度统计，对齐原版 StatUserJob。"""
    traffic = _normalize_traffic_data(data)
    if not traffic:
        return

    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        try:
            await _record_stat_user(db, traffic, float(_decimal_rate(server.get("rate", 1))), record_type)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def stat_server(
    ctx: dict,
    data: dict[str, Any],
    server: dict[str, Any],
    protocol: str,
    record_type: str = "d",
) -> None:
    """累计节点维度统计，对齐原版 StatServerJob。"""
    traffic = _normalize_traffic_data(data)
    if not traffic:
        return

    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        try:
            await _record_stat_server(db, int(server["id"]), protocol, traffic, record_type)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def _record_stat_user(
    db: AsyncSession,
    traffic: dict[int, tuple[int, int]],
    rate: float,
    record_type: str,
) -> None:
    record_at = _today_timestamp()
    user_ids = list(traffic.keys())
    stmt = (
        select(StatUser)
        .where(StatUser.record_at == record_at)
        .where(StatUser.server_rate == rate)
        .where(StatUser.user_id.in_(user_ids))  # type: ignore[attr-defined]
    )
    result = await db.execute(stmt)
    existing = {item.user_id: item for item in result.scalars().all()}
    for user_id, (upload, download) in traffic.items():
        item = existing.get(user_id)
        if item:
            item.u += upload
            item.d += download
        else:
            db.add(
                StatUser(
                    user_id=user_id,
                    server_rate=rate,
                    u=upload,
                    d=download,
                    record_type=record_type,
                    record_at=record_at,
                )
            )
    await db.flush()


async def _record_stat_server(
    db: AsyncSession,
    server_id: int,
    protocol: str,
    traffic: dict[int, tuple[int, int]],
    record_type: str,
) -> None:
    record_at = _today_timestamp()
    upload = sum(item[0] for item in traffic.values())
    download = sum(item[1] for item in traffic.values())
    stmt = (
        select(StatServer)
        .where(StatServer.record_at == record_at)
        .where(StatServer.server_id == server_id)
        .where(StatServer.server_type == protocol)
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item:
        item.u += upload
        item.d += download
    else:
        db.add(
            StatServer(
                server_id=server_id,
                server_type=protocol,
                u=upload,
                d=download,
                record_type=record_type,
                record_at=record_at,
            )
        )
    await db.flush()


def _normalize_traffic_data(data: dict[str, Any]) -> dict[int, tuple[int, int]]:
    traffic: dict[int, tuple[int, int]] = {}
    for raw_user_id, value in data.items():
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            continue
        try:
            if isinstance(value, dict):
                upload = int(value.get("u", value.get("upload", 0)))
                download = int(value.get("d", value.get("download", 0)))
            else:
                upload = int(value[0])
                download = int(value[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        traffic[user_id] = (upload, download)
    return traffic


def _decimal_rate(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("1")


def _today_timestamp() -> int:
    now = int(time.time())
    return now - (now % 86400)
