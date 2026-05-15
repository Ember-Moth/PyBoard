"""Ticket 字段全集，不含 id/关系/系统字段。对应 工单表 `ticket`。"""

from sqlmodel import Field, SQLModel


class TicketBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    user_id: int  # 用户 ID
    subject: str = Field(max_length=255)  # 工单主题
    level: int  # 紧急程度
    status: int = 0  # 0-已开启 1-已关闭
    reply_status: int = 0  # 0-待回复 1-已回复
