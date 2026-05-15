"""Auth 控制器 —— 注册、登录、当前用户。"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Request

from app.core.cache import RuntimeCache
from app.core.deps import CacheDep, get_auth_service, get_current_user
from app.core.queue import get_queue
from app.core.response_utils import created, success
from app.models.user.dto import EmailVerifyRequest, ForgetPasswordRequest, LoginRequest, TokenResponse, UserCreate, UserRead
from app.schemas.response import ApiResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[TokenResponse], status_code=201)
async def register(
    request: Request,
    data: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    """注册并返回 JWT。"""
    token = await service.register(data, request.client.host if request.client else None)
    return created(data=token)


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """登录并返回 JWT。"""
    token = await service.login(data)
    return success(data=token)


@router.get("/token2-login", response_model=ApiResponse[TokenResponse | str])
async def token2_login(
    verify: str | None = Query(None),
    token: str | None = Query(None),
    redirect: str = Query("dashboard"),
    cache: RuntimeCache = CacheDep,
    service: AuthService = Depends(get_auth_service),
):
    """使用一次性 token 登录，或生成前端 verify 跳转地址。"""
    if token:
        return success(data=f"/#/login?verify={token}&redirect={redirect or 'dashboard'}")
    if not verify:
        return success(data="")
    user_id = await cache.get(f"temp_token:{verify}")
    if user_id is None:
        return success(data="")
    await cache.delete(f"temp_token:{verify}")
    auth_token = await service.build_token_for_user_id(int(user_id))
    return success(data=auth_token)


@router.post("/forget", response_model=ApiResponse[bool])
async def forget_password(
    data: ForgetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """通过邮箱验证码重置密码。"""
    return success(data=await service.forget_password(data))


@router.post("/email-verify", response_model=ApiResponse[bool])
async def send_email_verify(
    request: Request,
    data: EmailVerifyRequest,
    service: AuthService = Depends(get_auth_service),
):
    """发送邮箱验证码。"""
    code = await service.create_email_verify_code(data, request.client.host if request.client else None)
    app_name = await service.setting_service.get_str("app_name", "PyBoard")
    app_url = await service.setting_service.get_str("app_url", "")
    try:
        queue = await get_queue()
        await queue.enqueue_job(
            "send_mail",
            data.email,
            f"{app_name} 邮箱验证码",
            "mail_verify",
            {"name": app_name, "code": code, "url": app_url},
        )
    except Exception:
        # 验证码已写入运行期缓存，队列不可用时不阻断业务请求，失败会由部署健康检查暴露。
        pass
    return success(data=True)


@router.post("/pv", response_model=ApiResponse[bool])
async def record_invite_pv(
    invite_code: Annotated[str | None, Body(embed=True)] = None,
    service: AuthService = Depends(get_auth_service),
):
    """记录邀请码访问次数。"""
    return success(data=await service.record_invite_pv(invite_code))


@router.get("/me", response_model=ApiResponse[UserRead])
async def me(current_user: UserRead = Depends(get_current_user)):
    """获取当前登录用户。"""
    return success(data=current_user)
