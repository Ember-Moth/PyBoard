"""ServerV2Node 数据库实体。对应 V2Ray 节点表 `server_v2node`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.server_v2node.base import ServerV2NodeBase


class ServerV2Node(ServerV2NodeBase, table=True):
    __tablename__ = "server_v2node"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
