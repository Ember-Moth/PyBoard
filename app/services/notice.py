"""Notice 服务层 —— 公告业务逻辑。"""

from app.core.exceptions import NotFoundException
from app.models.notice.dto import (
    NoticeCreate,
    NoticePublic,
    NoticeRead,
    NoticeUpdate,
)
from app.models.notice.entity import Notice
from app.repositories.notice import NoticeRepository
from app.schemas.response import PaginatedData


class NoticeService:
    """公告业务逻辑。"""

    def __init__(self, repo: NoticeRepository):
        self.repo = repo

    # ---- 用户端 ----
    async def list_public(self, page: int, size: int) -> PaginatedData[NoticePublic]:
        """用户端公告列表 —— 仅返回 show=True，按创建时间倒序。"""
        offset = (page - 1) * size
        items = await self.repo.list_visible(offset, size)
        total = await self.repo.count_visible()
        return PaginatedData(
            items=[_to_public(n) for n in items],
            total=total,
            page=page,
            size=size,
        )

    async def get_public(self, notice_id: int) -> NoticeRead:
        """用户端公告详情 —— 未上线 / 不存在均返回 404。"""
        notice = await self.repo.get_by_id(notice_id)
        if notice is None or not notice.show:
            raise NotFoundException(f"公告 {notice_id} 不存在")
        return _to_read(notice)

    # ---- 管理端 ----
    async def list_all(self, page: int, size: int) -> PaginatedData[NoticeRead]:
        """管理端公告列表 —— 全量，按 id 倒序。"""
        offset = (page - 1) * size
        items = await self.repo.list_all(offset, size)
        total = await self.repo.count()
        return PaginatedData(
            items=[_to_read(n) for n in items],
            total=total,
            page=page,
            size=size,
        )

    async def get(self, notice_id: int) -> NoticeRead:
        """管理端公告详情。"""
        notice = await self.repo.get_by_id(notice_id)
        if notice is None:
            raise NotFoundException(f"公告 {notice_id} 不存在")
        return _to_read(notice)

    async def create(self, data: NoticeCreate) -> NoticeRead:
        """创建公告。"""
        notice = Notice(**data.model_dump())
        notice = await self.repo.create(notice)
        return _to_read(notice)

    async def update(self, notice_id: int, data: NoticeUpdate) -> NoticeRead:
        """部分更新公告。"""
        notice = await self.repo.get_by_id(notice_id)
        if notice is None:
            raise NotFoundException(f"公告 {notice_id} 不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(notice, field, value)
        notice = await self.repo.update(notice)
        return _to_read(notice)

    async def delete(self, notice_id: int) -> None:
        """删除公告。"""
        notice = await self.repo.get_by_id(notice_id)
        if notice is None:
            raise NotFoundException(f"公告 {notice_id} 不存在")
        await self.repo.delete(notice)


def _to_public(n: Notice) -> NoticePublic:
    return NoticePublic.model_validate(n, from_attributes=True)


def _to_read(n: Notice) -> NoticeRead:
    return NoticeRead.model_validate(n, from_attributes=True)
