"""Notice 用户端控制器 —— 公告查询。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_notice_service
from app.core.response_utils import success
from app.models.notice.dto import NoticePublic, NoticeRead
from app.schemas.response import ApiResponse, PaginatedData
from app.services.notice import NoticeService

router = APIRouter(prefix="/api/v1/notices", tags=["公告"])


@router.get("", response_model=ApiResponse[PaginatedData[NoticePublic]])
async def list_notices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: NoticeService = Depends(get_notice_service),
):
    """已上线公告列表，按创建时间倒序。"""
    data = await service.list_public(page, size)
    return success(data=data)


@router.get("/{notice_id}", response_model=ApiResponse[NoticeRead])
async def get_notice(
    notice_id: int,
    service: NoticeService = Depends(get_notice_service),
):
    """公告详情（仅返回已上线公告）。"""
    notice = await service.get_public(notice_id)
    return success(data=notice)
