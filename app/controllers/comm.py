"""公共通信配置控制器。"""

from typing import Any

import orjson
from fastapi import APIRouter, Body, Depends, Request

from app.core.deps import get_current_user, get_payment_service, get_setting_service, get_telegram_service
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.response_utils import success
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.payment import PaymentService
from app.services.setting import SettingService
from app.services.telegram import TelegramService

common_router = APIRouter(prefix="/api/v1/common", tags=["公共配置"])
user_router = APIRouter(prefix="/api/v1/comm", tags=["公共配置"])
telegram_router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram"])


@common_router.get("/config", response_model=ApiResponse[dict])
async def common_config(service: SettingService = Depends(get_setting_service)):
    """获取前端公开配置。"""
    email_whitelist_enabled = await service.get_int("email_whitelist_enable", 0)
    site_config = (await service.fetch_config("site")).get("site", {})
    return success(
        data={
            **site_config,
            "tos_url": await service.get_str("tos_url", ""),
            "is_email_verify": 1 if await service.get_int("email_verify", 0) else 0,
            "is_invite_force": 1 if await service.get_int("invite_force", 0) else 0,
            "is_email_whitelist": 1 if email_whitelist_enabled else 0,
            "email_whitelist_suffix": await service.get_json("email_whitelist_suffix", []) if email_whitelist_enabled else 0,
            "is_recaptcha": 1 if await service.get_int("recaptcha_enable", 0) else 0,
            "recaptcha_provider": "turnstile",
            "recaptcha_site_key": await service.get_str("recaptcha_site_key", ""),
            "turnstile_site_key": await service.get_str("recaptcha_site_key", ""),
            "is_telegram": await service.get_int("telegram_bot_enable", 0),
            "telegram_discuss_link": await service.get_str("telegram_discuss_link", ""),
            "ticket_status": await service.get_int("ticket_status", 0),
            "stripe_pk": await service.get_str("stripe_pk_live", ""),
            "invite_gen_limit": await service.get_int("invite_gen_limit", 5),
            "withdraw_methods": await service.get_json("commission_withdraw_method", ["alipay", "usdt", "bank"]),
            "withdraw_close": await service.get_int("withdraw_close_enable", 0),
            "commission_withdraw_limit": await service.get_int("commission_withdraw_limit", 100),
            "currency": await service.get_str("currency", "CNY"),
            "currency_symbol": await service.get_str("currency_symbol", "¥"),
            "commission_distribution_enable": await service.get_int("commission_distribution_enable", 0),
            "commission_distribution_l1": await service.get_int("commission_distribution_l1", 0) or None,
            "commission_distribution_l2": await service.get_int("commission_distribution_l2", 0) or None,
            "commission_distribution_l3": await service.get_int("commission_distribution_l3", 0) or None,
        }
    )


@user_router.post("/stripe-public-key", response_model=ApiResponse[str])
async def get_stripe_public_key(
    payment_id: int = Body(..., embed=True, alias="id"),
    current_user: UserRead = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """获取 Stripe 支付方式公钥。"""
    _ = current_user
    payment = await service.get_payment(payment_id)
    if payment.payment != "StripeCredit":
        raise NotFoundException("支付方式不存在")
    config = _decode_config(payment.config)
    stripe_pk = config.get("stripe_pk_live") or config.get("stripe_pk") or config.get("public_key")
    if not stripe_pk:
        raise BadRequestException("支付方式未配置 Stripe 公钥")
    return success(data=str(stripe_pk))


@telegram_router.get("/bot", response_model=ApiResponse[dict])
async def get_telegram_bot_info(
    current_user: UserRead = Depends(get_current_user),
    service: TelegramService = Depends(get_telegram_service),
):
    """获取 Telegram Bot 信息。"""
    _ = current_user
    return success(data=await service.get_bot_info())


@telegram_router.post("/webhook", response_model=ApiResponse[bool])
async def telegram_webhook(
    request: Request,
    access_token: str,
    service: TelegramService = Depends(get_telegram_service),
):
    """接收 Telegram Webhook。"""
    payload = await request.json()
    return success(data=await service.handle_webhook(access_token, payload))


def _decode_config(config: Any) -> dict[str, Any]:
    if isinstance(config, dict):
        return config
    if not config:
        return {}
    try:
        value = orjson.loads(config)
    except orjson.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
