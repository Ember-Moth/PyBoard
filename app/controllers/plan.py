"""Plan 用户端控制器 —— 套餐查询。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_plan_service
from app.core.response_utils import success
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.plan import PlanService

router = APIRouter(prefix="/api/v1/plans", tags=["套餐"])


@router.get("", response_model=ApiResponse[list])
async def list_plans(service: PlanService = Depends(get_plan_service)):
    """已上线套餐列表。"""
    plans = await service.list_visible()
    return success(data=plans)


@router.get("/{plan_id}", response_model=ApiResponse)
async def get_plan(
    plan_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: PlanService = Depends(get_plan_service),
):
    """套餐详情（隐藏但可续费的套餐仅当前持有者可见）。"""
    plan = await service.get_for_user(plan_id, current_user.plan_id)
    return success(data=plan)
