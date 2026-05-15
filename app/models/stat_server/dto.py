"""StatServer DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class StatServerPublic(SQLModel):
    """节点数据统计列表公开视图。"""

    id: int
    created_at: int


class StatServerRead(SQLModel):
    """节点数据统计详情视图。"""

    id: int
    server_id: int
    server_type: str
    u: int
    d: int
    record_type: str
    record_at: int
    created_at: int
    updated_at: int
