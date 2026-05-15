"""支付 回调控制器 —— 处理支付网关回调。"""

import json

from fastapi import APIRouter, Depends, Request

from app.core.deps import get_order_service, get_payment_service
from app.core.response_utils import success
from app.schemas.response import ApiResponse
from app.services.order import OrderService
from app.services.payment import PaymentService

router = APIRouter(tags=["支付回调"])
methods_router = APIRouter(prefix="/api/v1/payment-methods", tags=["支付方式"])


@methods_router.get("", response_model=ApiResponse[list])
async def get_payment_methods(
    service: PaymentService = Depends(get_payment_service),
):
    """获取可用支付方式列表。"""
    methods = await service.get_enabled_methods()
    return success(data=methods)


@router.post("/notify/{gateway}/{uuid}")
async def payment_notify(
    gateway: str,
    uuid: str,
    request: Request,
    service: OrderService = Depends(get_order_service),
):
    """支付网关 JSON 回调。"""
    try:
        params = await request.json()
    except json.JSONDecodeError:
        return "fail"
    if not isinstance(params, dict):
        return "fail"

    result = await service.handle_payment_notify(gateway, uuid, params)
    return result
