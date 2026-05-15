"""Knowledge 数据库实体。对应 知识库表 `knowledge`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.knowledge.base import KnowledgeBase


class Knowledge(KnowledgeBase, table=True):
    __tablename__ = "knowledge"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
