"""统一日志事件写入工具。"""

import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_event.entity import LogEvent

_MAX_MESSAGE_LENGTH = 255
_MAX_STRING_LENGTHS = {
    "level": 16,
    "category": 32,
    "event": 64,
    "request_id": 64,
    "trace_id": 64,
    "actor_type": 32,
    "target_type": 32,
    "target_id": 64,
    "method": 11,
    "path": 255,
    "ip": 128,
    "user_agent": 255,
    "error_type": 128,
}


@dataclass(frozen=True)
class LogRetentionPolicy:
    """日志分类保留策略。

    retention_days 为 None 表示永久保留，不参与自动清理。
    protected=True 表示不允许通过管理端普通删除动作删除。
    """

    retention_days: int | None
    protected: bool = False


LOG_EVENT_RETENTION_POLICIES: dict[str, LogRetentionPolicy] = {
    "access": LogRetentionPolicy(retention_days=30),
    "queue": LogRetentionPolicy(retention_days=90),
    "mail": LogRetentionPolicy(retention_days=180),
    "system": LogRetentionPolicy(retention_days=180),
    "audit": LogRetentionPolicy(retention_days=None, protected=True),
    "commission": LogRetentionPolicy(retention_days=None, protected=True),
}


async def create_log_event(
    db: AsyncSession,
    *,
    event: str,
    message: str,
    level: str = "info",
    category: str = "access",
    request_id: str | None = None,
    trace_id: str | None = None,
    actor_type: str | None = None,
    actor_id: int | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    method: str | None = None,
    path: str | None = None,
    status_code: int | None = None,
    duration_ms: int | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    data: Any = None,
    error_type: str | None = None,
    error_stack: str | None = None,
) -> LogEvent:
    """创建一条日志事件。

    data 接收 dict/list/基础类型并直接写入 JSONB；调用方不需要手写 JSON。
    """
    item = LogEvent(
        level=_limit(level, "level") or "info",
        category=_limit(category, "category") or "access",
        event=_limit(event, "event") or "event",
        message=message[:_MAX_MESSAGE_LENGTH],
        request_id=_limit(request_id, "request_id"),
        trace_id=_limit(trace_id, "trace_id"),
        actor_type=_limit(actor_type, "actor_type"),
        actor_id=actor_id,
        target_type=_limit(target_type, "target_type"),
        target_id=_limit(target_id, "target_id"),
        method=_limit(method, "method"),
        path=_limit(path, "path"),
        status_code=status_code,
        duration_ms=duration_ms,
        ip=_limit(ip, "ip"),
        user_agent=_limit(user_agent, "user_agent"),
        data=data,
        error_type=_limit(error_type, "error_type"),
        error_stack=error_stack,
    )
    db.add(item)
    await db.flush()
    return item


async def cleanup_log_events_by_retention(db: AsyncSession, *, now: int | None = None) -> dict[str, int]:
    """按分类保留策略清理日志事件。

    只有声明了 retention_days 的分类会被清理；未知分类和受保护分类默认永久保留。
    """
    current = now or int(time.time())
    deleted: dict[str, int] = {}
    for category, policy in LOG_EVENT_RETENTION_POLICIES.items():
        if policy.retention_days is None:
            continue
        cutoff = current - policy.retention_days * 86400
        result = await db.execute(
            delete(LogEvent)
            .where(LogEvent.category == category)
            .where(LogEvent.created_at < cutoff)  # type: ignore[operator]
            .returning(LogEvent.id)
        )
        deleted[category] = len(result.scalars().all())
    return deleted


def is_protected_log_category(category: str) -> bool:
    """判断日志分类是否受保留策略保护。"""
    policy = LOG_EVENT_RETENTION_POLICIES.get(category)
    return bool(policy and policy.protected)


def _limit(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    length = _MAX_STRING_LENGTHS[field]
    return str(value)[:length]
