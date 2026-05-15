"""Notice DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class NoticePublic(SQLModel):
    """公告列表公开视图（用户端，不含 content / show / updated_at）。"""

    id: int
    title: str
    img_url: str | None = None
    tags: str | None = None
    created_at: int


class NoticeRead(SQLModel):
    """公告详情视图（管理端 / 用户端均可用）。"""

    id: int
    title: str
    content: str
    show: bool
    img_url: str | None = None
    tags: str | None = None
    created_at: int
    updated_at: int


class NoticeCreate(SQLModel):
    """创建公告（管理端）。"""

    title: str
    content: str
    show: bool = False
    img_url: str | None = None
    tags: str | None = None


class NoticeUpdate(SQLModel):
    """部分更新公告（管理端）。"""

    title: str | None = None
    content: str | None = None
    show: bool | None = None
    img_url: str | None = None
    tags: str | None = None
