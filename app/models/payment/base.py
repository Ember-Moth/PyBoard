"""Payment 字段全集，不含 id/关系/系统字段。对应 支付方式表 `payment`。"""

from typing import Any

from sqlmodel import Field, SQLModel

from app.models._columns import jsonb_object_field


class PaymentBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    uuid: str = Field(max_length=32)  # 支付方式 UUID
    payment: str = Field(max_length=16)  # 支付类型标识
    name: str = Field(max_length=255)  # 支付方式名称
    icon: str | None = Field(default=None, max_length=255)  # 图标 URL
    config: dict[str, Any] = jsonb_object_field()  # 支付配置 JSONB
    notify_domain: str | None = Field(default=None, max_length=128)  # 回调通知域名
    handling_fee_fixed: int | None = None  # 固定手续费
    handling_fee_percent: float | None = None  # 百分比手续费
    enable: bool = False  # 是否启用
    sort: int | None = None  # 排序权重
