"""StatServer 数据库实体。对应 节点数据统计表 `stat_server`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.stat_server.base import StatServerBase


class StatServer(StatServerBase, table=True):
    __tablename__ = "stat_server"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
