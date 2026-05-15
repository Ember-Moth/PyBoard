"""邮件接口视图，不做持久化。"""

from sqlmodel import SQLModel


class MailLogPublic(SQLModel):
    """邮件发送事件列表视图。"""

    id: int
    email: str
    subject: str
    template_name: str
    error: str | None
    created_at: int


class MailLogRead(SQLModel):
    """邮件发送事件详情视图。"""

    id: int
    email: str
    subject: str
    template_name: str
    error: str | None
    created_at: int
    updated_at: int


class MailSend(SQLModel):
    """发送邮件。"""

    email: str
    subject: str
    template_name: str
    template_value: dict | None = None
