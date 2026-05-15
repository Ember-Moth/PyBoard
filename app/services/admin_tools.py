"""管理端日志和失败任务 Service。"""

from typing import Any

import orjson

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.failed_job.dto import FailedJobPublic, FailedJobRead
from app.models.log_event.dto import LogEventPublic, LogEventRead
from app.repositories.failed_job import FailedJobRepository
from app.repositories.log_event import LogEventRepository
from app.services.log_event import is_protected_log_category


class LogService:
    """统一日志事件查询。"""

    def __init__(self, repo: LogEventRepository):
        self.repo = repo

    async def list_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        *,
        category: str | None = None,
        level: str | None = None,
        event: str | None = None,
        request_id: str | None = None,
        actor_id: int | None = None,
        ip: str | None = None,
        q: str | None = None,
    ) -> list[LogEventPublic]:
        items = await self.repo.list_all(
            offset,
            limit,
            category=category,
            level=level,
            event=event,
            request_id=request_id,
            actor_id=actor_id,
            ip=ip,
            q=q,
        )
        return [LogEventPublic.model_validate(item, from_attributes=True) for item in items]

    async def get_log(self, log_id: int) -> LogEventRead:
        item = await self.repo.get_by_id(log_id)
        if item is None:
            raise NotFoundException("日志不存在")
        return LogEventRead.model_validate(item, from_attributes=True)

    async def delete_log(self, log_id: int) -> None:
        item = await self.repo.get_by_id(log_id)
        if item is None:
            raise NotFoundException("日志不存在")
        if is_protected_log_category(item.category):
            raise BadRequestException("该日志分类受保留策略保护，不能手动删除")
        await self.repo.delete(item)


class FailedJobService:
    """失败队列任务查询和重试。"""

    def __init__(self, repo: FailedJobRepository):
        self.repo = repo

    async def list_jobs(self, offset: int = 0, limit: int = 50) -> list[FailedJobPublic]:
        items = await self.repo.list_all(offset, limit)
        return [FailedJobPublic.model_validate(item, from_attributes=True) for item in items]

    async def get_job(self, job_id: int) -> FailedJobRead:
        item = await self.repo.get_by_id(job_id)
        if item is None:
            raise NotFoundException("失败任务不存在")
        return FailedJobRead.model_validate(item, from_attributes=True)

    async def delete_job(self, job_id: int) -> None:
        item = await self.repo.get_by_id(job_id)
        if item is None:
            raise NotFoundException("失败任务不存在")
        await self.repo.delete(item)

    async def retry_job(self, job_id: int, queue: Any) -> bool:
        item = await self.repo.get_by_id(job_id)
        if item is None:
            raise NotFoundException("失败任务不存在")
        payload = item.payload
        if isinstance(payload, str):
            try:
                payload = orjson.loads(payload)
            except orjson.JSONDecodeError as exc:
                raise BadRequestException("失败任务载荷不是有效 JSON，无法重试") from exc
        if not isinstance(payload, dict):
            raise BadRequestException("失败任务载荷不是有效 JSON，无法重试")
        job_name = payload.get("job_name")
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        if not job_name:
            raise BadRequestException("失败任务缺少 job_name，无法重试")
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise BadRequestException("失败任务参数格式无效，无法重试")
        enqueue_kwargs = dict(kwargs)
        enqueue_kwargs.setdefault("_queue_name", item.queue)
        await queue.enqueue_job(job_name, *args, **enqueue_kwargs)
        await self.repo.delete(item)
        return True
