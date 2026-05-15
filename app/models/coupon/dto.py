"""Coupon DTO，接口视图，不做持久化。"""

from typing import Any

from sqlmodel import SQLModel


class CouponPublic(SQLModel):
    """优惠券列表公开视图。"""

    id: int
    code: str
    name: str
    type: int
    value: int
    show: bool
    started_at: int
    ended_at: int
    created_at: int


class CouponRead(SQLModel):
    """优惠券详情视图。"""

    id: int
    code: str
    name: str
    type: int
    value: int
    show: bool
    limit_use: int | None
    limit_use_with_user: int | None
    limit_plan_ids: str | None
    limit_period: str | None
    started_at: int
    ended_at: int
    created_at: int
    updated_at: int


class CouponCreate(SQLModel):
    """创建优惠券。"""

    code: str | None = None
    name: str
    type: int
    value: int
    show: bool = True
    limit_use: int | None = None
    limit_use_with_user: int | None = None
    limit_plan_ids: list[int] | str | None = None
    limit_period: list[str] | str | None = None
    started_at: int
    ended_at: int


class CouponUpdate(SQLModel):
    """更新优惠券。"""

    code: str | None = None
    name: str | None = None
    type: int | None = None
    value: int | None = None
    show: bool | None = None
    limit_use: int | None = None
    limit_use_with_user: int | None = None
    limit_plan_ids: list[int] | str | None = None
    limit_period: list[str] | str | None = None
    started_at: int | None = None
    ended_at: int | None = None


class CouponGenerate(SQLModel):
    """批量生成优惠券。"""

    name: str
    type: int
    value: int
    generate_count: int = 1
    show: bool = True
    limit_use: int | None = None
    limit_use_with_user: int | None = None
    limit_plan_ids: list[int] | str | None = None
    limit_period: list[str] | str | None = None
    started_at: int
    ended_at: int


class CouponCheck(SQLModel):
    """用户端优惠券校验。"""

    code: str
    plan_id: int
    period: str
    amount: int | None = None


class CouponCheckResult(SQLModel):
    """优惠券校验结果。"""

    coupon: CouponRead
    discount_amount: int | None = None
    extra: dict[str, Any] | None = None
