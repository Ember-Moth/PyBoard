"""ServerGroup 字段全集，不含 id/关系/系统字段。对应 服务器分组表 `server_group`。"""

from sqlmodel import Field, SQLModel


class ServerGroupBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    name: str = Field(max_length=255)  # 分组名称
