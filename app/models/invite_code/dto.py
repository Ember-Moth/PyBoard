"""InviteCode DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class InviteCodePublic(SQLModel):
    """邀请码列表公开视图。"""

    id: int
    user_id: int
    code: str
    status: int
    pv: int
    created_at: int


class InviteCodeRead(SQLModel):
    """邀请码详情视图。"""

    id: int
    user_id: int
    code: str
    status: int
    pv: int
    created_at: int
    updated_at: int


class InviteCodeCreate(SQLModel):
    """创建邀请码。"""

    user_id: int | None = None
    code: str | None = None
    status: int = 0


class InviteCodeUpdate(SQLModel):
    """更新邀请码。"""

    status: int | None = None
    pv: int | None = None
