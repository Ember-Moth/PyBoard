"""ServerRoute 字段全集，不含 id/关系/系统字段。对应 服务器路由规则表 `server_route`。"""

from typing import Any

from sqlmodel import Field, SQLModel

from app.models._columns import jsonb_field


class ServerRouteBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    remarks: str = Field(max_length=255)  # 备注
    match: Any = jsonb_field(nullable=False, default_factory=list)  # 匹配规则
    action: str = Field(max_length=11)  # 路由动作
    action_value: Any = jsonb_field()  # 动作参数
