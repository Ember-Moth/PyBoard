"""Telegram Bot 服务。"""

import hashlib
import re
import urllib.parse
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RuntimeCache
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.models.ticket.dto import TicketReply
from app.repositories.user import UserRepository
from app.services.setting import SettingService
from app.services.ticket import TicketService


class TelegramService:
    """处理 Telegram webhook 和基础命令。"""

    def __init__(
        self,
        db: AsyncSession,
        cache: RuntimeCache,
        setting_service: SettingService,
        ticket_service: TicketService,
    ):
        self.db = db
        self.cache = cache
        self.setting_service = setting_service
        self.ticket_service = ticket_service
        self.user_repo = UserRepository(db)

    async def get_bot_info(self) -> dict[str, Any]:
        token = await self._bot_token()
        if not token:
            return {"username": None}
        payload = await self._telegram_request(token, "getMe", {})
        return {"username": payload.get("result", {}).get("username") if payload.get("ok") else None}

    async def set_webhook(self, token: str, app_url: str) -> bool:
        access_token = hashlib.md5(token.encode()).hexdigest()
        hook_url = f"{app_url.rstrip('/')}/api/v1/telegram/webhook?access_token={access_token}"
        payload = await self._telegram_request(token, "setWebhook", {"url": hook_url})
        if not payload.get("ok"):
            raise BadRequestException(payload.get("description") or "Telegram webhook 设置失败")
        await self.setting_service.save_config("telegram_bot_token", token)
        return True

    async def handle_webhook(self, access_token: str, payload: dict[str, Any]) -> bool:
        token = await self._bot_token()
        if not token or access_token != hashlib.md5(token.encode()).hexdigest():
            raise UnauthorizedException()

        update_id = payload.get("update_id")
        if update_id is not None:
            await self.cache.set(f"telegram:update:{update_id}", payload, ex=86400)

        await self._handle_chat_join_request(token, payload.get("chat_join_request"))
        message = self._parse_message(payload.get("message"))
        if message:
            await self._handle_message(token, message)
        return True

    async def _handle_message(self, token: str, message: dict[str, Any]) -> None:
        text = message["text"]
        chat_id = message["chat_id"]
        command, *args = text.split()
        command = command.split("@", 1)[0].lower()

        try:
            if message.get("reply_text"):
                ticket_match = re.search(r"#(\d+)", message["reply_text"])
                if ticket_match:
                    await self._reply_ticket(token, chat_id, int(ticket_match.group(1)), text)
                    return
            if command == "/bind":
                await self._bind(token, chat_id, args[0] if args else "")
            elif command == "/unbind":
                await self._unbind(token, chat_id)
            elif command == "/traffic":
                await self._traffic(token, chat_id)
            elif command == "/getlatesturl":
                app_name = await self.setting_service.get_str("app_name", "PyBoard")
                app_url = await self.setting_service.get_str("app_url", "")
                await self._send_message(token, chat_id, f"{app_name}的最新网址是：{app_url}")
        except Exception as exc:
            await self._send_message(token, chat_id, str(exc))

    async def _bind(self, token: str, chat_id: int, raw_token: str) -> None:
        user_token = self._extract_user_token(raw_token)
        if not user_token:
            raise BadRequestException("参数有误，请携带 token 或订阅地址发送")
        user = await self.user_repo.get_by_token(user_token)
        if user is None:
            raise BadRequestException("用户不存在")
        if user.telegram_id:
            raise BadRequestException("该账号已经绑定了 Telegram 账号")
        user.telegram_id = chat_id
        await self.user_repo.update(user)
        await self._send_message(token, chat_id, "绑定成功")

    async def _unbind(self, token: str, chat_id: int) -> None:
        user = await self.user_repo.get_by_telegram_id(chat_id)
        if user is None:
            await self._send_message(token, chat_id, "没有查询到您的用户信息，请先绑定账号")
            return
        user.telegram_id = None
        await self.user_repo.update(user)
        await self._send_message(token, chat_id, "解绑成功")

    async def _traffic(self, token: str, chat_id: int) -> None:
        user = await self.user_repo.get_by_telegram_id(chat_id)
        if user is None:
            await self._send_message(token, chat_id, "没有查询到您的用户信息，请先绑定账号")
            return
        remaining = max(user.transfer_enable - user.u - user.d, 0)
        text = (
            "流量查询\n"
            f"计划流量：{_format_bytes(user.transfer_enable)}\n"
            f"已用上行：{_format_bytes(user.u)}\n"
            f"已用下行：{_format_bytes(user.d)}\n"
            f"剩余流量：{_format_bytes(remaining)}"
        )
        await self._send_message(token, chat_id, text)

    async def _reply_ticket(self, token: str, chat_id: int, ticket_id: int, text: str) -> None:
        user = await self.user_repo.get_by_telegram_id(chat_id)
        if user is None or not (user.is_admin or user.is_staff) or user.id is None:
            return
        await self.ticket_service.reply_admin_ticket(user.id, ticket_id, TicketReply(message=text))
        await self._send_message(token, chat_id, f"#{ticket_id} 的工单已回复成功")

    async def _handle_chat_join_request(self, token: str, request: dict[str, Any] | None) -> None:
        if not request:
            return
        chat_id = request.get("chat", {}).get("id")
        from_id = request.get("from", {}).get("id")
        if chat_id is None or from_id is None:
            return
        user = await self.user_repo.get_by_telegram_id(int(from_id))
        method = "approveChatJoinRequest" if user and not user.banned else "declineChatJoinRequest"
        await self._telegram_request(token, method, {"chat_id": chat_id, "user_id": from_id})

    def _parse_message(self, message: dict[str, Any] | None) -> dict[str, Any] | None:
        if not message or not message.get("text"):
            return None
        return {
            "text": message["text"],
            "chat_id": message.get("chat", {}).get("id"),
            "is_private": message.get("chat", {}).get("type") == "private",
            "reply_text": message.get("reply_to_message", {}).get("text"),
        }

    def _extract_user_token(self, raw_token: str) -> str:
        parsed = urllib.parse.urlparse(raw_token)
        if parsed.query:
            query = urllib.parse.parse_qs(parsed.query)
            return (query.get("token") or [""])[0]
        return raw_token.strip()

    async def _bot_token(self) -> str:
        return await self.setting_service.get_str("telegram_bot_token", "")

    async def _send_message(self, token: str, chat_id: int, text: str) -> bool:
        payload = {"chat_id": chat_id, "text": text}
        result = await self._telegram_request(token, "sendMessage", payload)
        return bool(result.get("ok"))

    async def _telegram_request(self, token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(f"https://api.telegram.org/bot{token}/{method}", json=payload)
            return response.json()
        except Exception:
            return {"ok": False}


def _format_bytes(value: int) -> str:
    size = float(max(value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.2f} PB"
