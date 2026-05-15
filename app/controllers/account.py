"""当前用户账户控制器。"""

import secrets
from typing import Annotated

from fastapi import APIRouter, Body, Depends

from app.core.cache import RuntimeCache
from app.core.deps import CacheDep, get_current_user, get_setting_service, get_stat_service, get_user_service
from app.core.response_utils import success
from app.models.user.dto import UserChangePassword, UserRead, UserSelfUpdate
from app.schemas.response import ApiResponse
from app.services.setting import SettingService
from app.services.stat import StatService
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/user", tags=["当前用户"])


@router.get("/info", response_model=ApiResponse[dict])
async def get_profile(
    current_user: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """获取当前用户资料。"""
    return success(data=await service.get_profile(current_user.id))


@router.get("/check-login", response_model=ApiResponse[dict])
async def check_login(current_user: UserRead = Depends(get_current_user)):
    """检查当前登录状态。"""
    data = {"is_login": True}
    if current_user.is_admin:
        data["is_admin"] = True
    if current_user.is_staff:
        data["is_staff"] = True
    return success(data=data)


@router.get("/stats", response_model=ApiResponse[list[int]])
async def get_account_stats(
    current_user: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """获取账户角标统计。"""
    return success(data=await service.get_account_stat(current_user.id))


@router.patch("/profile", response_model=ApiResponse[bool])
async def update_profile(
    data: UserSelfUpdate,
    current_user: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """更新当前用户偏好。"""
    return success(data=await service.update_profile(current_user.id, data))


@router.post("/change-password", response_model=ApiResponse[bool])
async def change_password(
    data: UserChangePassword,
    current_user: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """修改当前用户密码。"""
    return success(data=await service.change_password(current_user.id, data))


@router.post("/reset-security", response_model=ApiResponse[dict])
async def reset_security(
    current_user: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """重置用户安全标识。"""
    return success(data=await service.reset_security(current_user.id))


@router.post("/unbind-telegram", response_model=ApiResponse[bool])
async def unbind_telegram(
    current_user: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """解绑当前用户 Telegram。"""
    return success(data=await service.unbind_telegram(current_user.id))


@router.get("/traffic-logs", response_model=ApiResponse[list])
async def get_traffic_logs(
    limit: int = 30,
    current_user: UserRead = Depends(get_current_user),
    service: StatService = Depends(get_stat_service),
):
    """获取当前用户流量统计日志。"""
    return success(data=await service.user_traffic_log(current_user.id, limit))


@router.get("/active-sessions", response_model=ApiResponse[list])
async def get_active_sessions():
    """JWT 无状态认证没有服务端会话列表。"""
    return success(data=[])


@router.post("/active-sessions/remove", response_model=ApiResponse[bool])
async def remove_active_session():
    """JWT 无状态认证无需删除服务端会话。"""
    return success(data=True)


@router.post("/quick-login-url", response_model=ApiResponse[str])
async def get_quick_login_url(
    redirect: Annotated[str, Body(embed=True)] = "dashboard",
    current_user: UserRead = Depends(get_current_user),
    cache: RuntimeCache = CacheDep,
    setting_service: SettingService = Depends(get_setting_service),
):
    """生成一次性快速登录链接。"""
    code = secrets.token_urlsafe(24)
    await cache.set(f"temp_token:{code}", current_user.id, ex=60)
    app_url = (await setting_service.get_str("app_url", "")).rstrip("/")
    path = f"/#/login?verify={code}&redirect={redirect or 'dashboard'}"
    return success(data=f"{app_url}{path}" if app_url else path)
