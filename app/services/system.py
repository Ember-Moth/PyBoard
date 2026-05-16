"""系统状态和队列状态服务。"""

import platform
import shutil
import sys
import time
from typing import Any

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.failed_job.entity import FailedJob
from app.models.queue_job.entity import QueueJob
from app.queues.names import QUEUE_NAMES


class SystemService:
    """后台系统信息。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def status(self) -> dict[str, Any]:
        usage = shutil.disk_usage(".")
        return {
            "time": int(time.time()),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "disk": {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
            },
        }

    async def queue_stats(self) -> dict[str, Any]:
        queues = await self._queue_counts()
        failed = await self.db.execute(select(func.count()).select_from(FailedJob))
        return {
            "queues": queues,
            "failed_jobs": int(failed.scalar_one() or 0),
        }

    async def queue_workload(self) -> list[dict[str, Any]]:
        queues = await self._queue_counts()
        return [{"name": name, "jobs": queues[name]} for name in QUEUE_NAMES]

    async def _queue_counts(self) -> dict[str, int]:
        result = await self.db.execute(
            select(QueueJob.queue, func.count(QueueJob.id))
            .where(QueueJob.status.in_(["pending", "running"]))  # type: ignore[attr-defined]
            .group_by(QueueJob.queue)
        )
        queues = {name: 0 for name in QUEUE_NAMES}
        for name, count in result.all():
            if name in queues:
                queues[name] = int(count or 0)
        return queues
