"""Notice 管理端控制器 —— 公告 CRUD。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_notice_service
from app.core.response_utils import created, success
from app.models.notice.dto import NoticeCreate, NoticeRead, NoticeUpdate
from app.schemas.response import ApiResponse, PaginatedData
from app.services.notice import NoticeService

router = APIRouter(
    prefix="/api/v1/admin/notices",
    tags=["管理-公告"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[PaginatedData[NoticeRead]])
async def list_notices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: NoticeService = Depends(get_notice_service),
):
    """全量公告列表（含未上线），按 id 倒序。"""
    data = await service.list_all(page, size)
    return success(data=data)


@router.get("/{notice_id}", response_model=ApiResponse[NoticeRead])
async def get_notice(
    notice_id: int,
    service: NoticeService = Depends(get_notice_service),
):
    """公告详情。"""
    notice = await service.get(notice_id)
    return success(data=notice)


@router.post("", response_model=ApiResponse[NoticeRead], status_code=201)
async def create_notice(
    data: NoticeCreate,
    service: NoticeService = Depends(get_notice_service),
):
    """新建公告。"""
    notice = await service.create(data)
    return created(data=notice)


@router.patch("/{notice_id}", response_model=ApiResponse[NoticeRead])
async def update_notice(
    notice_id: int,
    data: NoticeUpdate,
    service: NoticeService = Depends(get_notice_service),
):
    """部分更新公告。"""
    notice = await service.update(notice_id, data)
    return success(data=notice)


@router.delete("/{notice_id}", status_code=204)
async def delete_notice(
    notice_id: int,
    service: NoticeService = Depends(get_notice_service),
):
    """删除公告。"""
    await service.delete(notice_id)
