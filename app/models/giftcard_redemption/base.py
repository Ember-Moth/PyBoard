"""礼品卡兑换记录字段。"""

from sqlmodel import Field, SQLModel


class GiftcardRedemptionBase(SQLModel):
    """礼品卡兑换记录，用于兑换幂等和审计。"""

    giftcard_id: int = Field(index=True)
    user_id: int = Field(index=True)
    code: str = Field(max_length=255)
    type: int
    value: int | None = None
    plan_id: int | None = None
