"""管理端系统状态接口。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin, get_system_service
from app.core.response_utils import success
from app.schemas.response import ApiResponse
from app.services.system import SystemService

router = APIRouter(
    prefix="/api/v1/admin/system",
    tags=["管理-系统"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/status", response_model=ApiResponse)
async def status(service: SystemService = Depends(get_system_service)):
    return success(data=await service.status())


@router.get("/queues", response_model=ApiResponse)
async def queue_stats(service: SystemService = Depends(get_system_service)):
    return success(data=await service.queue_stats())


@router.get("/queues/workload", response_model=ApiResponse[list])
async def queue_workload(service: SystemService = Depends(get_system_service)):
    return success(data=await service.queue_workload())
