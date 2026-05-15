"""CommissionLog 数据库实体。对应 佣金记录表 `commission_log`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.commission_log.base import CommissionLogBase


class CommissionLog(CommissionLogBase, table=True):
    __tablename__ = "commission_log"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
