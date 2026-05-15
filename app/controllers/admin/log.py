"""系统事件 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_log_service
from app.core.response_utils import success
from app.schemas.response import ApiResponse
from app.services.admin_tools import LogService

router = APIRouter(
    prefix="/api/v1/admin/logs",
    tags=["管理-日志"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = Query(None),
    level: str | None = Query(None),
    event: str | None = Query(None),
    request_id: str | None = Query(None),
    actor_id: int | None = Query(None),
    ip: str | None = Query(None),
    q: str | None = Query(None),
    service: LogService = Depends(get_log_service),
):
    logs = await service.list_logs(
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
    return success(data=logs)


@router.get("/{log_id}", response_model=ApiResponse[dict])
async def get_log(log_id: int, service: LogService = Depends(get_log_service)):
    log = await service.get_log(log_id)
    return success(data=log)


@router.delete("/{log_id}", status_code=204)
async def delete_log(log_id: int, service: LogService = Depends(get_log_service)):
    await service.delete_log(log_id)
