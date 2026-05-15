"""Stat 字段全集，不含 id/关系/系统字段。对应 订单统计表 `stat`。"""

from sqlmodel import Field, SQLModel


class StatBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    record_at: int = Field(unique=True)  # 统计日期
    record_type: str = Field(max_length=1)  # 统计类型
    order_count: int  # 订单数量
    order_total: int  # 订单合计金额
    commission_count: int  # 佣金笔数
    commission_total: int  # 佣金合计金额
    paid_count: int  # 已支付订单数
    paid_total: int  # 已支付合计金额
    register_count: int  # 注册用户数
    invite_count: int  # 邀请注册数
    transfer_used_total: str = Field(max_length=32)  # 已使用流量合计
