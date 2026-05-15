"""Coupon 数据库实体。对应 优惠券表 `coupon`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.coupon.base import CouponBase


class Coupon(CouponBase, table=True):
    __tablename__ = "coupon"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
