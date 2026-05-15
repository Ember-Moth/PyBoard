"""Stat 数据库实体。对应 订单统计表 `stat`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.stat.base import StatBase


class Stat(StatBase, table=True):
    __tablename__ = "stat"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
