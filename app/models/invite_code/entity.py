"""InviteCode 数据库实体。对应 邀请码表 `invite_code`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.invite_code.base import InviteCodeBase


class InviteCode(InviteCodeBase, table=True):
    __tablename__ = "invite_code"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
