"""礼品卡 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_giftcard_service
from app.core.response_utils import created, success
from app.models.giftcard.dto import GiftcardCreate, GiftcardGenerate, GiftcardUpdate
from app.schemas.response import ApiResponse
from app.services.giftcard import GiftcardService

router = APIRouter(
    prefix="/api/v1/admin/giftcards",
    tags=["管理-礼品卡"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_giftcards(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: GiftcardService = Depends(get_giftcard_service),
):
    giftcards = await service.list_all(offset, limit)
    return success(data=giftcards)


@router.get("/{giftcard_id}", response_model=ApiResponse[dict])
async def get_giftcard(giftcard_id: int, service: GiftcardService = Depends(get_giftcard_service)):
    giftcard = await service.get(giftcard_id)
    return success(data=giftcard)


@router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_giftcard(data: GiftcardCreate, service: GiftcardService = Depends(get_giftcard_service)):
    giftcard = await service.create(data)
    return created(data=giftcard)


@router.post("/generate", response_model=ApiResponse[list], status_code=201)
async def generate_giftcards(data: GiftcardGenerate, service: GiftcardService = Depends(get_giftcard_service)):
    giftcards = await service.generate(data)
    return created(data=giftcards)


@router.patch("/{giftcard_id}", response_model=ApiResponse[dict])
async def update_giftcard(
    giftcard_id: int,
    data: GiftcardUpdate,
    service: GiftcardService = Depends(get_giftcard_service),
):
    giftcard = await service.update(giftcard_id, data)
    return success(data=giftcard)


@router.delete("/{giftcard_id}", status_code=204)
async def delete_giftcard(giftcard_id: int, service: GiftcardService = Depends(get_giftcard_service)):
    await service.delete(giftcard_id)
