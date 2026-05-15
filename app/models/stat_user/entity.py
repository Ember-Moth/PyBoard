"""StatUser 数据库实体。对应 用户数据统计表 `stat_user`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.stat_user.base import StatUserBase


class StatUser(StatUserBase, table=True):
    __tablename__ = "stat_user"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
