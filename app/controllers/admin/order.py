"""订单 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_order_service
from app.core.response_utils import success
from app.models.order.dto import AdminOrderAssign, AdminOrderTradeNo, AdminOrderUpdate
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.order import OrderService

router = APIRouter(
    prefix="/api/v1/admin/orders",
    tags=["管理-订单"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_orders(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: OrderService = Depends(get_order_service),
):
    """获取订单列表（管理端）。"""
    orders = await service.list_orders(offset, limit)
    return success(data=orders)


@router.get("/{order_id}", response_model=ApiResponse[dict])
async def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
):
    """获取订单详情（管理端）。"""
    order = await service.get_order_detail_admin(order_id)
    return success(data=order)


@router.patch("", response_model=ApiResponse[bool])
async def update_order(
    data: AdminOrderUpdate,
    current_admin: UserRead = Depends(get_current_admin),
    service: OrderService = Depends(get_order_service),
):
    """更新订单字段（管理端）。"""
    return success(data=await service.admin_update_order(data, actor_id=current_admin.id))


@router.post("/assign", response_model=ApiResponse[str])
async def assign_order(
    data: AdminOrderAssign,
    current_admin: UserRead = Depends(get_current_admin),
    service: OrderService = Depends(get_order_service),
):
    """给用户分配订单（管理端）。"""
    return success(data=await service.admin_assign_order(data, actor_id=current_admin.id))


@router.post("/paid", response_model=ApiResponse[bool])
async def mark_order_paid(
    data: AdminOrderTradeNo,
    current_admin: UserRead = Depends(get_current_admin),
    service: OrderService = Depends(get_order_service),
):
    """手动标记订单为已支付（管理端）。"""
    return success(data=await service.admin_mark_paid(data.trade_no, actor_id=current_admin.id))


@router.post("/cancel", response_model=ApiResponse[bool])
async def cancel_order(
    data: AdminOrderTradeNo,
    current_admin: UserRead = Depends(get_current_admin),
    service: OrderService = Depends(get_order_service),
):
    """取消订单（管理端）。"""
    return success(data=await service.admin_cancel_order(data.trade_no, actor_id=current_admin.id))
