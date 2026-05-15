"""Telegram 队列任务，对齐原版 SendTelegramJob。"""

import asyncio
import urllib.parse
import urllib.request

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_engine
from app.models.setting.entity import Setting
from sqlmodel import select


async def send_telegram(ctx: dict, telegram_id: int, text: str, parse_mode: str = "markdown") -> None:
    """发送 Telegram 消息。"""
    token = await _load_bot_token()
    if not token:
        raise RuntimeError("Telegram Bot Token 未配置")
    if parse_mode == "markdown":
        text = text.replace("_", "\\_")
    await asyncio.to_thread(_send_sync, token, telegram_id, text, parse_mode)


async def _load_bot_token() -> str:
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        result = await db.execute(select(Setting.value).where(Setting.key == "telegram_bot_token"))
        return result.scalar_one_or_none() or ""


def _send_sync(token: str, telegram_id: int, text: str, parse_mode: str) -> None:
    payload = urllib.parse.urlencode(
        {
            "chat_id": telegram_id,
            "text": text,
            "parse_mode": parse_mode,
        }
    ).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
        if response.status >= 400:
            raise RuntimeError(f"Telegram 发送失败: HTTP {response.status}")
