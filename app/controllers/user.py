"""User 控制器 —— 用户相关 API 路由。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin, get_user_service
from app.core.response_utils import created, success
from app.models.user.dto import (
    AdminUserBan,
    AdminUserGenerate,
    AdminUserInviteSetter,
    UserCreate,
    UserPublic,
    UserRead,
    UserUpdate,
)
from app.schemas.response import ApiResponse
from app.services.user import UserService

router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["管理-用户"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list[UserPublic]])
async def list_users(
    offset: int = 0,
    limit: int = 100,
    q: str | None = None,
    status: str | None = None,
    service: UserService = Depends(get_user_service),
):
    """查询用户列表。"""
    users = await service.list_users(offset, limit, q, status)
    return success(data=users)


@router.get("/{user_id}", response_model=ApiResponse[UserRead])
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """查询用户详情。"""
    user = await service.get_user(user_id)
    return success(data=user)


@router.post("", response_model=ApiResponse[UserRead], status_code=201)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """创建新用户。"""
    user = await service.create_user(data)
    return created(data=user)


@router.post("/generate", response_model=ApiResponse[list], status_code=201)
async def generate_users(
    data: AdminUserGenerate,
    service: UserService = Depends(get_user_service),
):
    """批量生成用户。"""
    users = await service.admin_generate_users(data)
    return created(data=users)


@router.patch("/{user_id}", response_model=ApiResponse[UserRead])
async def update_user(
    user_id: int,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    """部分更新用户。"""
    user = await service.update_user(user_id, data)
    return success(data=user)


@router.post("/{user_id}/ban", response_model=ApiResponse[bool])
async def ban_user(
    user_id: int,
    data: AdminUserBan,
    service: UserService = Depends(get_user_service),
):
    """封禁或解封用户。"""
    return success(data=await service.admin_set_banned(user_id, data))


@router.post("/{user_id}/reset-security", response_model=ApiResponse[bool])
async def reset_user_security(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """重置用户订阅 token 与 UUID。"""
    return success(data=await service.admin_reset_security(user_id))


@router.post("/{user_id}/invite-user", response_model=ApiResponse[bool])
async def set_invite_user(
    user_id: int,
    data: AdminUserInviteSetter,
    service: UserService = Depends(get_user_service),
):
    """设置用户邀请人。"""
    return success(data=await service.admin_set_invite_user(user_id, data))


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """删除用户。删除成功不返回 body。"""
    await service.delete_user(user_id)
