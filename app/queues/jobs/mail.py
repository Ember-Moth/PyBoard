"""邮件相关任务。"""

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

from jinja2 import TemplateNotFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.core.database import get_engine
from app.models.setting.entity import Setting
from app.services.log_event import create_log_event
from app.utils.template import render


async def send_mail(
    ctx: dict,
    email: str,
    subject: str,
    template_name: str,
    template_value: dict[str, Any] | None = None,
) -> None:
    """发送邮件。

    Args:
        email: 收件邮箱
        subject: 邮件主题
        template_name: 模板名称
    """
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        error: str | None = None
        error_type: str | None = None
        try:
            settings = await _load_settings(db)
            await _send_email(email, subject, template_name, template_value or {}, settings)
        except Exception as exc:
            error = str(exc)
            error_type = type(exc).__name__
        await create_log_event(
            db,
            level="error" if error else "info",
            category="mail",
            event="mail.failed" if error else "mail.sent",
            message=subject,
            target_type="email",
            target_id=email,
            data={
                "email": email,
                "subject": subject,
                "template_name": template_name,
                "error": error,
            },
            error_type=error_type,
        )
        await db.commit()
        if error:
            raise RuntimeError(error)


async def _load_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(Setting))
    return {item.key: item.value for item in result.scalars().all()}


async def _send_email(
    email: str,
    subject: str,
    template_name: str,
    template_value: dict[str, Any],
    settings: dict[str, str],
) -> None:
    host = settings.get("email_host", "")
    port = int(settings.get("email_port", "0") or 0)
    username = settings.get("email_username", "")
    password = settings.get("email_password", "")
    encryption = settings.get("email_encryption", "").lower()
    from_address = settings.get("email_from_address", "")
    app_name = settings.get("app_name", "PyBoard")
    if not host or not port or not from_address:
        raise RuntimeError("邮件 SMTP 配置不完整")
    template_value.setdefault("name", app_name)
    try:
        body = render(f"mail/{template_name}", **template_value)
    except TemplateNotFound as exc:
        raise RuntimeError("邮件模板不存在") from exc

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = email
    message.set_content(body, subtype="html")
    await asyncio.to_thread(_send_sync, host, port, username, password, encryption, message)


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
