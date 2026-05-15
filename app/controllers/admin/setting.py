"""Setting 管理端控制器 —— 系统配置 CRUD + PyBoard 分组结构。"""

from pathlib import Path

from fastapi import APIRouter, Body, Depends

from app.core.deps import get_current_admin, get_mail_service, get_setting_service, get_telegram_service
from app.core.exceptions import BadRequestException
from app.core.response_utils import created, success
from app.models.mail.dto import MailSend
from app.models.setting.dto import SettingCreate, SettingPublic, SettingRead, SettingUpdate
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.mail import MailService
from app.services.setting import SettingService
from app.services.telegram import TelegramService

router = APIRouter(
    prefix="/api/v1/admin/settings",
    tags=["管理-系统配置"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/groups", response_model=ApiResponse[dict])
async def list_setting_groups(
    service: SettingService = Depends(get_setting_service),
):
    """获取全部分组配置。"""
    config = await service.fetch_config()
    return success(data=config)


@router.get("/groups/{group_key}", response_model=ApiResponse[dict])
async def get_setting_group(
    group_key: str,
    service: SettingService = Depends(get_setting_service),
):
    """获取指定分组配置。"""
    result = await service.fetch_config(group_key)
    if not result:
        return success(data={})
    return success(data=result)


@router.put("/values", response_model=ApiResponse[bool])
async def save_setting_value(
    key: str = Body(..., description="配置项 key，如 app_name"),
    value: str | int | bool | dict | list = Body(..., description="配置值"),
    service: SettingService = Depends(get_setting_service),
):
    """保存单个配置项，自动判断类型。"""
    await service.save_config(key, value)
    return success(data=True)


@router.put("/values/batch", response_model=ApiResponse[bool])
async def batch_save_setting_values(
    items: dict[str, str | int | bool | dict | list] = Body(...),
    service: SettingService = Depends(get_setting_service),
):
    """批量保存多个配置项。"""
    await service.batch_save_config(items)
    return success(data=True)


@router.get("/templates/email", response_model=ApiResponse[list[str]])
async def list_email_templates():
    """获取邮件模板文件列表。"""
    path = Path("app/templates/mail")
    files = sorted(item.name for item in path.glob("*.html") if item.is_file())
    return success(data=files)


@router.post("/mail/test", response_model=ApiResponse[bool])
async def test_send_mail(
    current_user: UserRead = Depends(get_current_admin),
    mail_service: MailService = Depends(get_mail_service),
    setting_service: SettingService = Depends(get_setting_service),
):
    """向当前管理员发送测试邮件。"""
    app_name = await setting_service.get_str("app_name", "PyBoard")
    result = await mail_service.send(
        MailSend(
            email=current_user.email,
            subject="This is PyBoard test email",
            template_name="system_notify",
            template_value={
                "name": app_name,
                "content": "This is PyBoard test email",
                "url": await setting_service.get_str("app_url", ""),
            },
        )
    )
    return success(data=result)


@router.post("/telegram/webhook", response_model=ApiResponse[bool])
async def set_telegram_webhook(
    telegram_bot_token: str = Body(..., embed=True),
    service: SettingService = Depends(get_setting_service),
    telegram_service: TelegramService = Depends(get_telegram_service),
):
    """设置 Telegram webhook。"""
    token = telegram_bot_token or await service.get_str("telegram_bot_token", "")
    app_url = (await service.get_str("app_url", "")).rstrip("/")
    if not token or not app_url:
        raise BadRequestException("telegram_bot_token 或 app_url 未配置")
    return success(data=await telegram_service.set_webhook(token, app_url))


@router.get("", response_model=ApiResponse[list[SettingPublic]])
async def list_settings(
    offset: int = 0,
    limit: int = 100,
    service: SettingService = Depends(get_setting_service),
):
    """系统配置列表（不含 value）。"""
    items = await service.list_settings(offset, limit)
    return success(data=items)


@router.get("/{setting_id}", response_model=ApiResponse[SettingRead])
async def get_setting(
    setting_id: int,
    service: SettingService = Depends(get_setting_service),
):
    """系统配置详情（含 value）。"""
    item = await service.get_setting(setting_id)
    return success(data=item)


@router.post("", response_model=ApiResponse[SettingRead], status_code=201)
async def create_setting(
    data: SettingCreate,
    service: SettingService = Depends(get_setting_service),
):
    """创建系统配置。"""
    item = await service.create_setting(data)
    return created(data=item)


@router.patch("/{setting_id}", response_model=ApiResponse[SettingRead])
async def update_setting(
    setting_id: int,
    data: SettingUpdate,
    service: SettingService = Depends(get_setting_service),
):
    """更新系统配置。"""
    item = await service.update_setting(setting_id, data)
    return success(data=item)


@router.delete("/{setting_id}", status_code=204)
async def delete_setting(
    setting_id: int,
    service: SettingService = Depends(get_setting_service),
):
    """删除系统配置。"""
    await service.delete_setting(setting_id)
