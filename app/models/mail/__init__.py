"""邮件 DTO 统一出口。"""

from app.models.mail.dto import MailLogPublic, MailLogRead, MailSend

__all__ = [
    "MailLogPublic",
    "MailLogRead",
    "MailSend",
]
