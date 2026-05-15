"""邮件 Service。"""

import asyncio
import smtplib
from email.message import EmailMessage

from jinja2 import TemplateNotFound

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.log_event.entity import LogEvent
from app.models.mail.dto import MailLogPublic, MailLogRead, MailSend
from app.repositories.log_event import LogEventRepository
from app.services.log_event import create_log_event
from app.services.setting import SettingService
from app.utils.template import render


class MailService:
    """邮件发送和日志查询。"""

    def __init__(self, repo: LogEventRepository, setting_service: SettingService):
        self.repo = repo
        self.setting_service = setting_service

    async def list_logs(self, offset: int = 0, limit: int = 50) -> list[MailLogPublic]:
        items = await self.repo.list_all(offset, limit, category="mail")
        return [_mail_log_public(item) for item in items]

    async def get_log(self, log_id: int) -> MailLogRead:
        item = await self.repo.get_by_id(log_id)
        if item is None or item.category != "mail":
            raise NotFoundException("邮件日志不存在")
        return _mail_log_read(item)

    async def send(self, data: MailSend) -> bool:
        error: str | None = None
        error_type: str | None = None
        try:
            await self._send_email(data)
        except Exception as exc:
            error = str(exc)
            error_type = type(exc).__name__
        await self._write_mail_event(data, error=error, error_type=error_type)
        return error is None

    async def _write_mail_event(self, data: MailSend, *, error: str | None, error_type: str | None) -> None:
        event = "mail.failed" if error else "mail.sent"
        await create_log_event(
            self.repo.db,
            level="error" if error else "info",
            category="mail",
            event=event,
            message=data.subject,
            target_type="email",
            target_id=data.email,
            data={
                "email": data.email,
                "subject": data.subject,
                "template_name": data.template_name,
                "error": error,
            },
            error_type=error_type,
        )

    async def _send_email(self, data: MailSend) -> None:
        host = await self.setting_service.get_str("email_host", "")
        port = await self.setting_service.get_int("email_port", 0)
        username = await self.setting_service.get_str("email_username", "")
        password = await self.setting_service.get_str("email_password", "")
        encryption = (await self.setting_service.get_str("email_encryption", "")).lower()
        from_address = await self.setting_service.get_str("email_from_address", "")
        app_name = await self.setting_service.get_str("app_name", "PyBoard")

        if not host or not port or not from_address:
            raise BadRequestException("邮件 SMTP 配置不完整")

        context = data.template_value or {}
        context.setdefault("name", app_name)
        try:
            body = render(f"mail/{data.template_name}", **context)
        except TemplateNotFound as exc:
            raise BadRequestException("邮件模板不存在") from exc

        message = EmailMessage()
        message["Subject"] = data.subject
        message["From"] = from_address
        message["To"] = data.email
        message.set_content(body, subtype="html")

        await asyncio.to_thread(
            _send_sync,
            host,
            port,
            username,
            password,
            encryption,
            message,
        )


def _send_sync(
    host: str,
    port: int,
    username: str,
    password: str,
    encryption: str,
    message: EmailMessage,
) -> None:
    if encryption == "ssl":
        smtp: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        smtp = smtplib.SMTP(host, port, timeout=15)
    with smtp:
        if encryption == "tls":
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(message)


def _mail_log_public(item: LogEvent) -> MailLogPublic:
    data = _mail_data(item)
    return MailLogPublic(
        id=int(item.id or 0),
        email=data["email"],
        subject=data["subject"],
        template_name=data["template_name"],
        error=data["error"],
        created_at=int(item.created_at or 0),
    )


def _mail_log_read(item: LogEvent) -> MailLogRead:
    data = _mail_data(item)
    return MailLogRead(
        id=int(item.id or 0),
        email=data["email"],
        subject=data["subject"],
        template_name=data["template_name"],
        error=data["error"],
        created_at=int(item.created_at or 0),
        updated_at=int(item.updated_at or 0),
    )


def _mail_data(item: LogEvent) -> dict[str, str | None]:
    data = item.data if isinstance(item.data, dict) else {}
    return {
        "email": str(data.get("email") or item.target_id or ""),
        "subject": str(data.get("subject") or item.message or ""),
        "template_name": str(data.get("template_name") or ""),
        "error": str(data["error"]) if data.get("error") is not None else None,
    }
