"""Notice 数据库实体。对应 公告表 `notice`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.notice.base import NoticeBase


class Notice(NoticeBase, table=True):
    __tablename__ = "notice"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
