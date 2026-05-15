"""ServerGroup DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class ServerGroupCreate(SQLModel):
    name: str


class ServerGroupUpdate(SQLModel):
    name: str | None = None


class ServerGroupPublic(SQLModel):
    """服务器分组列表公开视图。"""

    id: int
    created_at: int


class ServerGroupRead(SQLModel):
    """服务器分组详情视图。"""

    id: int
    name: str
    created_at: int
    updated_at: int
