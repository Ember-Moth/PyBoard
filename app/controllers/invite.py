"""邀请返利 用户端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, get_invite_service
from app.core.response_utils import created, success
from app.models.commission_log.dto import CommissionTransfer
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.commission import InviteService

router = APIRouter(prefix="/api/v1/invite", tags=["邀请返利"])


@router.get("", response_model=ApiResponse[dict])
async def fetch_invite(
    current_user: UserRead = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
):
    """获取邀请码和佣金概览。"""
    result = await service.fetch(current_user.id)
    return success(data=result)


@router.post("/codes", response_model=ApiResponse[dict], status_code=201)
async def create_invite_code(
    current_user: UserRead = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
):
    """生成邀请码。"""
    result = await service.create_for_user(current_user.id)
    return created(data=result)


@router.get("/commission-logs", response_model=ApiResponse[list])
async def list_commission_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserRead = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
):
    """获取当前用户佣金明细。"""
    logs = await service.list_commission_logs(current_user.id, offset, limit)
    return success(data=logs)


@router.post("/commission/transfer", response_model=ApiResponse[bool])
async def transfer_commission(
    data: CommissionTransfer,
    current_user: UserRead = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
):
    """佣金划转到余额。"""
    result = await service.transfer_commission(current_user.id, data)
    return success(data=result)
