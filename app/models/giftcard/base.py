"""Giftcard 字段全集，不含 id/关系/系统字段。对应 礼品卡表 `giftcard`。"""

from sqlmodel import Field, SQLModel


class GiftcardBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    code: str = Field(max_length=255)  # 礼品卡码
    name: str = Field(max_length=255)  # 礼品卡名称
    type: int  # 类型
    value: int | None = None  # 面值
    plan_id: int | None = None  # 绑定套餐 ID
    limit_use: int | None = None  # 总使用次数限制
    used_user_ids: str | None = Field(default=None, max_length=16384)  # 已使用用户 ID 列表
    started_at: int  # 生效时间
    ended_at: int  # 失效时间
