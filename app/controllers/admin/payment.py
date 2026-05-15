"""支付方式 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_payment_service
from app.core.response_utils import created, success
from app.models.payment.dto import PaymentCreate, PaymentUpdate
from app.schemas.response import ApiResponse
from app.services.payment import PaymentService

router = APIRouter(
    prefix="/api/v1/admin/payment-methods",
    tags=["管理-支付方式"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_payments(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: PaymentService = Depends(get_payment_service),
):
    """获取支付方式列表。"""
    payments = await service.list_payments(offset, limit)
    return success(data=payments)


@router.get("/gateways", response_model=ApiResponse[list])
async def list_payment_gateways(
    service: PaymentService = Depends(get_payment_service),
):
    """获取后端已注册的支付网关和配置表单。"""
    gateways = service.list_gateways()
    return success(data=gateways)


@router.get("/{payment_id}", response_model=ApiResponse[dict])
async def get_payment(
    payment_id: int,
    service: PaymentService = Depends(get_payment_service),
):
    """获取支付方式详情。"""
    payment = await service.get_payment(payment_id)
    return success(data=payment)


@router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_payment(
    data: PaymentCreate,
    service: PaymentService = Depends(get_payment_service),
):
    """创建支付方式。"""
    payment = await service.create_payment(data)
    return created(data=payment)


@router.patch("/{payment_id}", response_model=ApiResponse[dict])
async def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    service: PaymentService = Depends(get_payment_service),
):
    """更新支付方式。"""
    payment = await service.update_payment(payment_id, data)
    return success(data=payment)


@router.delete("/{payment_id}", status_code=204)
async def delete_payment(
    payment_id: int,
    service: PaymentService = Depends(get_payment_service),
):
    """删除支付方式。"""
    await service.delete_payment(payment_id)
