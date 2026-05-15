"""邀请返利 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_invite_service
from app.core.response_utils import created, success
from app.models.invite_code.dto import InviteCodeCreate, InviteCodeUpdate
from app.schemas.response import ApiResponse
from app.services.commission import InviteService

router = APIRouter(
    prefix="/api/v1/admin/invite",
    tags=["管理-邀请返利"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/codes", response_model=ApiResponse[list])
async def list_invite_codes(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: InviteService = Depends(get_invite_service),
):
    codes = await service.admin_list_invite_codes(offset, limit)
    return success(data=codes)


@router.post("/codes", response_model=ApiResponse[dict], status_code=201)
async def create_invite_code(
    data: InviteCodeCreate,
    service: InviteService = Depends(get_invite_service),
):
    code = await service.admin_create_invite_code(data)
    return created(data=code)


@router.patch("/codes/{invite_id}", response_model=ApiResponse[dict])
async def update_invite_code(
    invite_id: int,
    data: InviteCodeUpdate,
    service: InviteService = Depends(get_invite_service),
):
    code = await service.admin_update_invite_code(invite_id, data)
    return success(data=code)


@router.delete("/codes/{invite_id}", status_code=204)
async def delete_invite_code(invite_id: int, service: InviteService = Depends(get_invite_service)):
    await service.admin_delete_invite_code(invite_id)


@router.get("/commission-logs", response_model=ApiResponse[list])
async def list_commission_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: InviteService = Depends(get_invite_service),
):
    logs = await service.admin_list_commission_logs(offset, limit)
    return success(data=logs)
