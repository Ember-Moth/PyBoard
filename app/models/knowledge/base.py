"""Knowledge 字段全集，不含 id/关系/系统字段。对应 知识库表 `knowledge`。"""

from sqlmodel import Field, SQLModel


class KnowledgeBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    language: str = Field(max_length=5)  # 语言
    category: str = Field(max_length=255)  # 分类名
    title: str = Field(max_length=255)  # 标题
    body: str  # 内容
    sort: int | None = None  # 排序
    show: bool = False  # 是否显示
