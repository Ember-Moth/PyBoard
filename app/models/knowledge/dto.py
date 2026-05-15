"""Knowledge DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class KnowledgePublic(SQLModel):
    """知识库列表公开视图（用户端，不含 body / show）。"""

    id: int
    language: str
    category: str
    title: str
    sort: int | None = None
    updated_at: int


class KnowledgeRead(SQLModel):
    """知识库详情视图。"""

    id: int
    language: str
    category: str
    title: str
    body: str
    sort: int | None = None
    show: bool
    created_at: int
    updated_at: int


class KnowledgeCreate(SQLModel):
    """创建知识（管理端）。"""

    language: str
    category: str
    title: str
    body: str
    sort: int | None = None
    show: bool = False


class KnowledgeUpdate(SQLModel):
    """部分更新知识（管理端）。"""

    language: str | None = None
    category: str | None = None
    title: str | None = None
    body: str | None = None
    sort: int | None = None
    show: bool | None = None
