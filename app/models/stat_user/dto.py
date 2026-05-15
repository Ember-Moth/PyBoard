"""StatUser DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class StatUserPublic(SQLModel):
    """用户数据统计列表公开视图。"""

    id: int
    created_at: int


class StatUserRead(SQLModel):
    """用户数据统计详情视图。"""

    id: int
    user_id: int
    server_rate: float
    u: int
    d: int
    record_type: str
    record_at: int
    created_at: int
    updated_at: int
