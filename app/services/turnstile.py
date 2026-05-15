"""Cloudflare Turnstile verification service."""

from typing import Any

import httpx

from app.core.exceptions import BadRequestException
from app.services.setting import SettingService

TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_MAX_TOKEN_LENGTH = 2048


class TurnstileService:
    """Verify public auth form submissions with Cloudflare Turnstile."""

    def __init__(self, setting_service: SettingService):
        self.setting_service = setting_service

    async def verify_if_enabled(self, token: str | None, remote_ip: str | None = None) -> None:
        """Verify a Turnstile token when recaptcha_enable is enabled."""
        if not await self.setting_service.get_int("recaptcha_enable", 0):
            return

        secret = await self.setting_service.get_str("recaptcha_key", "")
        if not secret:
            raise BadRequestException("Turnstile Secret Key 未配置")

        token = (token or "").strip()
        if not token or len(token) > _MAX_TOKEN_LENGTH:
            raise BadRequestException("请完成人机验证")

        payload: dict[str, Any] = {
            "secret": secret,
            "response": token,
        }
        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(TURNSTILE_SITEVERIFY_URL, data=payload)
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            raise BadRequestException("人机验证服务暂不可用，请稍后重试") from exc

        if not isinstance(result, dict) or not result.get("success"):
            raise BadRequestException("人机验证失败，请重试")
