"""TicketMessage 字段全集，不含 id/关系/系统字段。对应 工单消息表 `ticket_message`。"""

from sqlmodel import SQLModel


class TicketMessageBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    user_id: int  # 发送者用户 ID
    ticket_id: int  # 所属工单 ID
    message: str  # 消息内容
