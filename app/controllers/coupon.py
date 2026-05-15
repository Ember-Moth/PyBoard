"""优惠券 用户端控制器。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_coupon_service, get_current_user
from app.core.response_utils import success
from app.models.coupon.dto import CouponCheck
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.coupon import CouponService

router = APIRouter(prefix="/api/v1/coupons", tags=["优惠券"])


@router.post("/check", response_model=ApiResponse[dict])
async def check_coupon(
    data: CouponCheck,
    current_user: UserRead = Depends(get_current_user),
    service: CouponService = Depends(get_coupon_service),
):
    """校验优惠券并返回可抵扣金额。"""
    result = await service.check(current_user.id, data)
    return success(data=result)
