"""礼品卡兑换记录实体。"""

from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field

from app.models.giftcard_redemption.base import GiftcardRedemptionBase


class GiftcardRedemption(GiftcardRedemptionBase, table=True):
    __tablename__ = "giftcard_redemption"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint(
            "giftcard_id",
            "user_id",
            name="uq_giftcard_redemption_giftcard_user",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
