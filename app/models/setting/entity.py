"""Setting 数据库实体。"""

from sqlmodel import Field
from app.models._columns import created_at_field, updated_at_field

from app.models.setting.base import SettingBase


class Setting(SettingBase, table=True):
    __tablename__ = "setting"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: int | None = created_at_field()
    updated_at: int | None = updated_at_field()
