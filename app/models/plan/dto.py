"""Plan DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class PlanPublic(SQLModel):
    """订阅套餐列表公开视图（用户端）。

    capacity_limit 为剩余容量（总容量 - 活跃用户数）。
    """

    id: int
    group_id: int
    transfer_enable: int
    device_limit: int | None
    name: str
    speed_limit: int | None
    sort: int | None
    content: str | None
    month_price: int | None
    quarter_price: int | None
    half_year_price: int | None
    year_price: int | None
    two_year_price: int | None
    three_year_price: int | None
    onetime_price: int | None
    reset_price: int | None
    reset_traffic_method: int | None
    capacity_limit: int | None  # 剩余容量
    created_at: int


class PlanRead(SQLModel):
    """订阅套餐详情视图（用户端）。"""

    id: int
    group_id: int
    transfer_enable: int
    device_limit: int | None
    name: str
    speed_limit: int | None
    sort: int | None
    renew: bool
    content: str | None
    month_price: int | None
    quarter_price: int | None
    half_year_price: int | None
    year_price: int | None
    two_year_price: int | None
    three_year_price: int | None
    onetime_price: int | None
    reset_price: int | None
    reset_traffic_method: int | None
    capacity_limit: int | None  # 剩余容量
    created_at: int
    updated_at: int


class PlanAdminRead(SQLModel):
    """订阅套餐详情视图（管理端），附带活跃用户计数。"""

    id: int
    group_id: int
    transfer_enable: int
    device_limit: int | None
    name: str
    speed_limit: int | None
    show: bool
    sort: int | None
    renew: bool
    content: str | None
    month_price: int | None
    quarter_price: int | None
    half_year_price: int | None
    year_price: int | None
    two_year_price: int | None
    three_year_price: int | None
    onetime_price: int | None
    reset_price: int | None
    reset_traffic_method: int | None
    capacity_limit: int | None  # 总容量
    count: int  # 活跃用户数
    created_at: int
    updated_at: int


class PlanCreate(SQLModel):
    """创建套餐（管理端）。"""

    group_id: int
    transfer_enable: int
    device_limit: int | None = None
    name: str
    speed_limit: int | None = None
    show: bool = False
    sort: int | None = None
    renew: bool = True
    content: str | None = None
    month_price: int | None = None
    quarter_price: int | None = None
    half_year_price: int | None = None
    year_price: int | None = None
    two_year_price: int | None = None
    three_year_price: int | None = None
    onetime_price: int | None = None
    reset_price: int | None = None
    reset_traffic_method: int | None = None
    capacity_limit: int | None = None


class PlanUpdate(SQLModel):
    """部分更新套餐（管理端）。"""

    group_id: int | None = None
    transfer_enable: int | None = None
    device_limit: int | None = None
    name: str | None = None
    speed_limit: int | None = None
    show: bool | None = None
    sort: int | None = None
    renew: bool | None = None
    content: str | None = None
    month_price: int | None = None
    quarter_price: int | None = None
    half_year_price: int | None = None
    year_price: int | None = None
    two_year_price: int | None = None
    three_year_price: int | None = None
    onetime_price: int | None = None
    reset_price: int | None = None
    reset_traffic_method: int | None = None
    capacity_limit: int | None = None
