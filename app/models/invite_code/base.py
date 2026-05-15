"""InviteCode 字段全集，不含 id/关系/系统字段。对应 邀请码表 `invite_code`。"""

from sqlmodel import Field, SQLModel


class InviteCodeBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    user_id: int  # 所属用户 ID
    code: str = Field(max_length=32)  # 邀请码
    status: int = 0  # 状态
    pv: int = 0  # 邀请页面访问量
