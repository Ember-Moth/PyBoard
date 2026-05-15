"""Plan 数据库实体。对应 订阅套餐表 `plan`。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field
from app.models.plan.base import PlanBase


class Plan(PlanBase, table=True):
    __tablename__ = "plan"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
