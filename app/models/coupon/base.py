"""Coupon 字段全集，不含 id/关系/系统字段。对应 优惠券表 `coupon`。"""

from sqlmodel import Field, SQLModel


class CouponBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    code: str = Field(max_length=255)  # 优惠券码
    name: str = Field(max_length=255)  # 优惠券名称
    type: int  # 类型
    value: int  # 面值/折扣值
    show: bool = False  # 是否展示
    limit_use: int | None = None  # 总使用次数限制
    limit_use_with_user: int | None = None  # 单用户使用次数限制
    limit_plan_ids: str | None = Field(default=None, max_length=255)  # 限制适用套餐
    limit_period: str | None = Field(default=None, max_length=255)  # 限制适用周期
    started_at: int  # 生效时间
    ended_at: int  # 失效时间
