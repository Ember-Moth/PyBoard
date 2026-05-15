"""Plan 字段全集，不含 id/关系/系统字段。对应 订阅套餐表 `plan`。"""

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class PlanBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    group_id: int  # 套餐所属服务器组 ID
    transfer_enable: int = Field(sa_type=BigInteger)  # 可用流量上限 (byte)
    device_limit: int | None = None  # 设备数量限制
    name: str = Field(max_length=255)  # 套餐名称
    speed_limit: int | None = None  # 速度限制
    show: bool = False  # 是否前端展示
    sort: int | None = None  # 排序权重
    renew: bool = True  # 是否允许续费
    content: str | None = None  # 套餐描述内容
    month_price: int | None = None  # 月付价格
    quarter_price: int | None = None  # 季付价格
    half_year_price: int | None = None  # 半年付价格
    year_price: int | None = None  # 年付价格
    two_year_price: int | None = None  # 两年付价格
    three_year_price: int | None = None  # 三年付价格
    onetime_price: int | None = None  # 一次性价格
    reset_price: int | None = None  # 重置流量价格
    reset_traffic_method: int | None = None  # 重置流量方式
    capacity_limit: int | None = None  # 容量限制
