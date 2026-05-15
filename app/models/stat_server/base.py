"""StatServer 字段全集，不含 id/关系/系统字段。对应 节点数据统计表 `stat_server`。"""

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class StatServerBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    server_id: int = Field(index=True)  # 节点 ID
    server_type: str = Field(max_length=11)  # 节点类型
    u: int = Field(sa_type=BigInteger)  # 上行流量 (byte)
    d: int = Field(sa_type=BigInteger)  # 下行流量 (byte)
    record_type: str = Field(max_length=1)  # 记录类型 d-日 m-月
    record_at: int = Field(index=True)  # 记录时间
