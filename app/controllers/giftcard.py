"""礼品卡 用户端控制器。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_giftcard_service
from app.core.response_utils import success
from app.models.giftcard.dto import GiftcardRedeem
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.giftcard import GiftcardService

router = APIRouter(prefix="/api/v1/giftcards", tags=["礼品卡"])


@router.post("/redeem", response_model=ApiResponse[dict])
async def redeem_giftcard(
    data: GiftcardRedeem,
    current_user: UserRead = Depends(get_current_user),
    service: GiftcardService = Depends(get_giftcard_service),
):
    """兑换礼品卡。"""
    result = await service.redeem(current_user.id, data.code)
    return success(data=result)
