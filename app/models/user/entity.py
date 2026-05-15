"""User 数据库实体 —— 只加 id、系统字段和关系。"""

from sqlalchemy.orm import foreign
from sqlmodel import Field, Relationship
from app.models._columns import created_at_field, updated_at_field

from app.models.order.entity import Order
from app.models.ticket.entity import Ticket
from app.models.user.base import UserBase


class User(UserBase, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()

    # ---- 逻辑外键 Relationship（不生成物理 FK） ----
    orders: list[Order] = Relationship(  # type: ignore[assignment]
        sa_relationship_kwargs={
            "primaryjoin": lambda: User.id == foreign(Order.user_id),  # type: ignore[arg-type]
            "foreign_keys": lambda: [Order.user_id],
            "viewonly": True,
        },
    )
    tickets: list[Ticket] = Relationship(  # type: ignore[assignment]
        sa_relationship_kwargs={
            "primaryjoin": lambda: User.id == foreign(Ticket.user_id),  # type: ignore[arg-type]
            "foreign_keys": lambda: [Ticket.user_id],
            "viewonly": True,
        },
    )
