"""Setting DTO。"""

from sqlmodel import SQLModel


class SettingCreate(SQLModel):
    """创建配置。"""

    key: str
    value: str
    type: str = "str"
    description: str | None = None


class SettingUpdate(SQLModel):
    """更新配置。"""

    value: str | None = None
    type: str | None = None
    description: str | None = None


class SettingPublic(SQLModel):
    """列表展示。"""

    id: int
    key: str
    type: str
    description: str | None
    updated_at: int


class SettingRead(SettingPublic):
    """详情（含 value）。"""

    value: str
