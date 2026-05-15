"""Admin 系统配置 HTML 路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.admin_ui.deps import (
    action_error,
    current_admin,
    form_data,
    page,
    redirect_to_login,
    template,
    unauthorized_fragment,
    valid_csrf,
    validation_error_message,
)
from app.admin_ui.forms import setting_group_values_from_form
from app.core.deps import get_auth_service, get_mail_service, get_setting_service, get_telegram_service
from app.core.exceptions import AppException
from app.models.mail.dto import MailSend
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.mail import MailService
from app.services.setting import SettingService
from app.services.telegram import TelegramService

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/settings.html.j2", request, admin, "settings", "系统配置")


@router.get("/fragments/settings/groups", response_class=HTMLResponse, include_in_schema=False)
async def settings_groups(
    request: Request,
    active_group: str | None = None,
    auth: AuthService = Depends(get_auth_service),
    setting_service: SettingService = Depends(get_setting_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await settings_groups_response(request, admin, setting_service, active_group)


@router.post("/actions/settings/groups/{group_key}", response_class=HTMLResponse, include_in_schema=False)
async def save_setting_group_action(
    group_key: str,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    setting_service: SettingService = Depends(get_setting_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await setting_service.batch_save_config(setting_group_values_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await settings_groups_response(request, admin, setting_service, group_key)
    response.headers["HX-Trigger"] = "admin:toast"
    return response


@router.post("/actions/settings/mail/test", response_class=HTMLResponse, include_in_schema=False)
async def test_mail_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    mail_service: MailService = Depends(get_mail_service),
    setting_service: SettingService = Depends(get_setting_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    app_name = await setting_service.get_str("app_name", "PyBoard")
    ok = await mail_service.send(
        MailSend(
            email=admin.email,
            subject="This is PyBoard test email",
            template_name="system_notify",
            template_value={
                "name": app_name,
                "content": "This is PyBoard test email",
                "url": await setting_service.get_str("app_url", ""),
            },
        )
    )
    return template("admin/fragments/action_error.html.j2", request, {"message": "测试邮件发送成功" if ok else "测试邮件发送失败"})


@router.post("/actions/settings/telegram/webhook", response_class=HTMLResponse, include_in_schema=False)
async def telegram_webhook_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    setting_service: SettingService = Depends(get_setting_service),
    telegram_service: TelegramService = Depends(get_telegram_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    token = str(form.get("telegram_bot_token") or await setting_service.get_str("telegram_bot_token", ""))
    app_url = (await setting_service.get_str("app_url", "")).rstrip("/")
    if not token or not app_url:
        return action_error(request, "telegram_bot_token 或 app_url 未配置")
    try:
        ok = await telegram_service.set_webhook(token, app_url)
    except AppException as exc:
        return action_error(request, exc.detail)
    return template("admin/fragments/action_error.html.j2", request, {"message": "Telegram Webhook 设置成功" if ok else "Telegram Webhook 设置失败"})


async def settings_groups_response(
    request: Request,
    admin: UserRead,
    setting_service: SettingService,
    active_group: str | None = None,
):
    config = await setting_service.fetch_config()
    active_group = active_group if active_group in config else next(iter(config.keys()), "site")
    return template(
        "admin/fragments/settings_groups.html.j2",
        request,
        {"admin": admin, "config": config, "active_group": active_group},
    )
