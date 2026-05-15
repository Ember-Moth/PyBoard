"""Giftcard 模型统一出口。"""

from app.models.giftcard.dto import (
    GiftcardCreate,
    GiftcardGenerate,
    GiftcardPublic,
    GiftcardRead,
    GiftcardRedeem,
    GiftcardRedeemResult,
    GiftcardUpdate,
)
from app.models.giftcard.entity import Giftcard

__all__ = [
    "Giftcard",
    "GiftcardCreate",
    "GiftcardGenerate",
    "GiftcardPublic",
    "GiftcardRead",
    "GiftcardRedeem",
    "GiftcardRedeemResult",
    "GiftcardUpdate",
]
