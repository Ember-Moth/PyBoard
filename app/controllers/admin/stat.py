"""管理端统计接口。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin, get_stat_service
from app.core.response_utils import success
from app.schemas.response import ApiResponse
from app.services.stat import StatService

router = APIRouter(
    prefix="/api/v1/admin/stats",
    tags=["管理-统计"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/overview", response_model=ApiResponse)
async def overview(service: StatService = Depends(get_stat_service)):
    return success(data=await service.overview())


@router.get("/orders", response_model=ApiResponse[list])
async def order_series(limit: int = 30, service: StatService = Depends(get_stat_service)):
    return success(data=await service.order_series(limit))


@router.get("/servers/rank", response_model=ApiResponse[list])
async def server_rank(
    period: str = "today",
    limit: int = 15,
    service: StatService = Depends(get_stat_service),
):
    return success(data=await service.server_rank(period, limit))


@router.get("/users/rank", response_model=ApiResponse[list])
async def user_rank(
    period: str = "today",
    limit: int = 30,
    service: StatService = Depends(get_stat_service),
):
    return success(data=await service.user_rank(period, limit))


@router.get("/users/{user_id}/traffic", response_model=ApiResponse[list])
async def user_traffic(
    user_id: int,
    limit: int = 30,
    service: StatService = Depends(get_stat_service),
):
    return success(data=await service.user_traffic_log(user_id, limit))
