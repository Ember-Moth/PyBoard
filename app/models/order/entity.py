"""Order 数据库实体。对应 订单表 `orders`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.order.base import OrderBase


class Order(OrderBase, table=True):
    __tablename__ = "orders"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
