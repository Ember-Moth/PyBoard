"""ServerGroup 数据库实体。对应 服务器分组表 `server_group`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.server_group.base import ServerGroupBase


class ServerGroup(ServerGroupBase, table=True):
    __tablename__ = "server_group"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
