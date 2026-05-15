"""StatUser 字段全集，不含 id/关系/系统字段。对应 用户数据统计表 `stat_user`。"""

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class StatUserBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    user_id: int = Field(index=True)  # 用户 ID
    server_rate: float  # 节点倍率
    u: int = Field(sa_type=BigInteger)  # 上行流量 (byte)
    d: int = Field(sa_type=BigInteger)  # 下行流量 (byte)
    record_type: str = Field(max_length=2)  # 记录类型
    record_at: int = Field(index=True)  # 记录时间
