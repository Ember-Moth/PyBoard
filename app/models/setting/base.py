"""Setting 字段全集。"""

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class SettingBase(SQLModel):
    """所有业务字段定义在此。"""

    key: str = Field(max_length=64, unique=True)  # 配置键
    value: str = Field(sa_column=Column(Text, nullable=False))  # 配置值
    type: str = Field(default="str", max_length=8)  # str / int / bool / json
    description: str | None = Field(default=None, max_length=255)  # 说明
