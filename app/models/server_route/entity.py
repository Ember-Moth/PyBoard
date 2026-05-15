"""ServerRoute 数据库实体。对应 服务器路由规则表 `server_route`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.server_route.base import ServerRouteBase


class ServerRoute(ServerRouteBase, table=True):
    __tablename__ = "server_route"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
