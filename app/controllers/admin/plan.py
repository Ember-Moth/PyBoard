"""Plan 管理端控制器 —— 套餐 CRUD。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin, get_plan_service
from app.core.response_utils import created, success
from app.models.plan.dto import PlanCreate, PlanUpdate
from app.schemas.response import ApiResponse
from app.services.plan import PlanService

router = APIRouter(
    prefix="/api/v1/admin/plans",
    tags=["管理-套餐"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_plans(service: PlanService = Depends(get_plan_service)):
    """全量套餐列表（含未上线），附带活跃用户计数。"""
    plans = await service.list_all()
    return success(data=plans)


@router.get("/{plan_id}", response_model=ApiResponse)
async def get_plan(
    plan_id: int,
    service: PlanService = Depends(get_plan_service),
):
    plan = await service.get(plan_id)
    return success(data=plan)


@router.post("", response_model=ApiResponse, status_code=201)
async def create_plan(
    data: PlanCreate,
    service: PlanService = Depends(get_plan_service),
):
    plan = await service.create(data)
    return created(data=plan)


@router.patch("/{plan_id}", response_model=ApiResponse)
async def update_plan(
    plan_id: int,
    data: PlanUpdate,
    service: PlanService = Depends(get_plan_service),
):
    plan = await service.update(plan_id, data)
    return success(data=plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: int,
    service: PlanService = Depends(get_plan_service),
):
    """安全删除 —— 有订单或活跃用户时拒绝删除。"""
    await service.delete(plan_id)
