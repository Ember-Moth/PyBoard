"""优惠券 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_coupon_service, get_current_admin
from app.core.response_utils import created, success
from app.models.coupon.dto import CouponCreate, CouponGenerate, CouponUpdate
from app.schemas.response import ApiResponse
from app.services.coupon import CouponService

router = APIRouter(
    prefix="/api/v1/admin/coupons",
    tags=["管理-优惠券"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_coupons(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: CouponService = Depends(get_coupon_service),
):
    coupons = await service.list_all(offset, limit)
    return success(data=coupons)


@router.get("/{coupon_id}", response_model=ApiResponse[dict])
async def get_coupon(coupon_id: int, service: CouponService = Depends(get_coupon_service)):
    coupon = await service.get(coupon_id)
    return success(data=coupon)


@router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_coupon(data: CouponCreate, service: CouponService = Depends(get_coupon_service)):
    coupon = await service.create(data)
    return created(data=coupon)


@router.post("/generate", response_model=ApiResponse[list], status_code=201)
async def generate_coupons(data: CouponGenerate, service: CouponService = Depends(get_coupon_service)):
    coupons = await service.generate(data)
    return created(data=coupons)


@router.patch("/{coupon_id}", response_model=ApiResponse[dict])
async def update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    service: CouponService = Depends(get_coupon_service),
):
    coupon = await service.update(coupon_id, data)
    return success(data=coupon)


@router.post("/{coupon_id}/toggle", response_model=ApiResponse[dict])
async def toggle_coupon(coupon_id: int, service: CouponService = Depends(get_coupon_service)):
    coupon = await service.toggle_show(coupon_id)
    return success(data=coupon)


@router.delete("/{coupon_id}", status_code=204)
async def delete_coupon(coupon_id: int, service: CouponService = Depends(get_coupon_service)):
    await service.delete(coupon_id)
