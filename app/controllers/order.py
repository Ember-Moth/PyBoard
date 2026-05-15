"""订单 用户端控制器。"""

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user, get_order_service
from app.core.response_utils import success
from app.models.order.dto import OrderCheckout, OrderCreate
from app.schemas.response import ApiResponse
from app.services.order import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["订单"])


@router.get("", response_model=ApiResponse[list])
async def list_orders(
    status: int | None = Query(None, description="订单状态筛选"),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """获取用户订单列表。"""
    orders = await service.get_user_orders(current_user.id, status)
    return success(data=orders)


@router.get("/detail", response_model=ApiResponse[dict])
async def get_order_detail(
    trade_no: str = Query(..., description="交易号"),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """获取订单详情。"""
    detail = await service.get_order_detail(trade_no, current_user.id)
    return success(data=detail)


@router.post("", response_model=ApiResponse[str])
async def create_order(
    data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """创建订单。"""
    trade_no = await service.create_order(current_user.id, data)
    return success(data=trade_no)


@router.post("/checkout", response_model=ApiResponse[dict])
async def checkout(
    data: OrderCheckout,
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """订单结账。"""
    result = await service.checkout(current_user.id, data.trade_no, data.method)
    return success(data=result)


@router.get("/check", response_model=ApiResponse[int])
async def check_order_status(
    trade_no: str = Query(..., description="交易号"),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """检查订单状态。"""
    status = await service.check_order_status(trade_no, current_user.id)
    return success(data=status)


@router.post("/cancel", response_model=ApiResponse[bool])
async def cancel_order(
    trade_no: str = Body(..., embed=True, description="交易号"),
    current_user: dict = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """取消订单。"""
    result = await service.cancel_order(trade_no, current_user.id)
    return success(data=result)
