"""Payment 数据库实体。对应 支付方式表 `payment`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.payment.base import PaymentBase


class Payment(PaymentBase, table=True):
    __tablename__ = "payment"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
