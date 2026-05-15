"""Giftcard 数据库实体。对应 礼品卡表 `giftcard`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.giftcard.base import GiftcardBase


class Giftcard(GiftcardBase, table=True):
    __tablename__ = "giftcard"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
