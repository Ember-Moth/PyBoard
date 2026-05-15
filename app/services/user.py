"""User 服务层 —— 用户业务逻辑。"""

import hashlib
import secrets
import string
import uuid

from sqlalchemy import update
from sqlmodel import delete, select

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.invite_code.entity import InviteCode
from app.models.order.entity import Order
from app.models.ticket.entity import Ticket
from app.models.ticket_message.entity import TicketMessage
from app.models.user.dto import (
    AdminUserBan,
    AdminUserGenerate,
    AdminUserInviteSetter,
    UserChangePassword,
    UserCreate,
    UserPublic,
    UserRead,
    UserSelfUpdate,
    UserUpdate,
)
from app.models.user.entity import User
from app.repositories.plan import PlanRepository
from app.repositories.user import UserRepository
from app.utils.password import hash_password, verify_and_upgrade


class UserService:
    """用户业务逻辑，依赖 Repository 接口（方便测试 mock）。"""

    def __init__(self, repo: UserRepository, plan_repo: PlanRepository):
        self.repo = repo
        self.plan_repo = plan_repo

    # ---- 查询 ----
    async def list_users(
        self,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        status: str | None = None,
    ) -> list[UserPublic]:
        """查询用户列表，返回脱敏后的公开数据。"""
        users = await self.repo.search_users(offset, limit, q, status)
        return [_to_public(u) for u in users]

    async def get_user(self, user_id: int) -> UserRead:
        """查询用户详情。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"用户 {user_id} 不存在")
        return _to_read(user)

    async def get_profile(self, user_id: int) -> dict:
        """获取当前用户账户资料。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        return {
            "email": user.email,
            "transfer_enable": user.transfer_enable,
            "device_limit": user.device_limit,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "banned": user.banned,
            "auto_renewal": user.auto_renewal,
            "remind_expire": user.remind_expire,
            "remind_traffic": user.remind_traffic,
            "expired_at": user.expired_at,
            "balance": user.balance,
            "commission_balance": user.commission_balance,
            "plan_id": user.plan_id,
            "discount": user.discount,
            "commission_rate": user.commission_rate,
            "telegram_id": user.telegram_id,
            "uuid": user.uuid,
            "avatar_url": f"https://cravatar.cn/avatar/{hashlib.md5(user.email.encode()).hexdigest()}?s=64&d=identicon",
        }

    async def get_account_stat(self, user_id: int) -> list[int]:
        """获取账户角标统计：[待支付订单, 开启工单, 邀请人数]。"""
        if await self.repo.get_by_id(user_id) is None:
            raise NotFoundException("用户不存在")
        return [
            await self.repo.count_pending_orders(user_id),
            await self.repo.count_open_tickets(user_id),
            await self.repo.count_invited_users(user_id),
        ]

    # ---- 写操作 ----
    async def create_user(self, data: UserCreate) -> UserRead:
        """注册新用户，created_at / updated_at 由 Repository 自动设置。"""
        if await self.repo.email_exists(data.email):
            raise ConflictException("邮箱已注册")
        user = User(
            email=data.email,
            password=hash_password(data.password),
            token=secrets.token_hex(16),
            uuid=secrets.token_hex(18),
        )
        user = await self.repo.create(user)
        return _to_read(user)

    async def update_user(self, user_id: int, data: UserUpdate) -> UserRead:
        """更新用户资料（部分更新），updated_at 由 Repository 自动刷新。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"用户 {user_id} 不存在")
        updates = data.model_dump(exclude_unset=True)
        if "email" in updates:
            email = updates["email"]
            if email is None:
                updates.pop("email")
            elif email != user.email and await self.repo.email_exists(email):
                raise ConflictException("邮箱已注册")
        if "password" in updates:
            password = updates.pop("password")
            if password is not None:
                user.password = hash_password(password)
        for field, value in updates.items():
            setattr(user, field, value)
        user = await self.repo.update(user)
        return _to_read(user)

    async def update_profile(self, user_id: int, data: UserSelfUpdate) -> bool:
        """更新当前用户偏好。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.repo.update(user)
        return True

    async def change_password(self, user_id: int, data: UserChangePassword) -> bool:
        """当前用户修改密码。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        valid, new_hash = verify_and_upgrade(data.old_password, user.password)
        if not valid:
            raise BadRequestException("旧密码错误")
        user.password = hash_password(data.new_password)
        _ = new_hash
        await self.repo.update(user)
        return True

    async def reset_security(self, user_id: int) -> dict[str, str]:
        """重置用户安全标识。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        user.uuid = str(uuid.uuid4())
        user.token = secrets.token_hex(16)
        await self.repo.update(user)
        return {"uuid": user.uuid, "token": user.token}

    async def admin_reset_security(self, user_id: int) -> bool:
        """管理端重置用户安全标识。"""
        await self.reset_security(user_id)
        return True

    async def admin_set_banned(self, user_id: int, data: AdminUserBan) -> bool:
        """管理端封禁/解封用户。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        user.banned = data.banned
        await self.repo.update(user)
        return True

    async def admin_set_invite_user(self, user_id: int, data: AdminUserInviteSetter) -> bool:
        """管理端设置邀请人。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        if not data.invite_user_email:
            user.invite_user_id = None
        else:
            invite_user = await self.repo.get_by_email(data.invite_user_email.strip().lower())
            if invite_user is None or invite_user.id == user.id:
                raise BadRequestException("邀请人无效")
            user.invite_user_id = invite_user.id
        await self.repo.update(user)
        return True

    async def admin_generate_users(self, data: AdminUserGenerate) -> list[dict]:
        """管理端批量生成用户。"""
        if not data.email_suffix or "@" in data.email_suffix:
            raise BadRequestException("邮箱后缀格式不正确")
        count = data.generate_count or 1
        if count < 1 or count > 500:
            raise BadRequestException("生成数量必须在 1-500 之间")

        plan = None
        if data.plan_id:
            plan = await self.plan_repo.get_by_id(data.plan_id)
            if plan is None:
                raise NotFoundException("套餐不存在")

        generated: list[dict] = []
        for index in range(count):
            prefix = data.email_prefix.strip().lower() if data.email_prefix else _random_prefix()
            if count > 1 and data.email_prefix:
                prefix = f"{prefix}{index + 1}"
            email = f"{prefix}@{data.email_suffix.strip().lower().lstrip('@')}"
            if await self.repo.email_exists(email):
                raise ConflictException(f"邮箱 {email} 已存在")
            password = data.password or email
            user = User(
                email=email,
                password=hash_password(password),
                token=secrets.token_hex(16),
                uuid=str(uuid.uuid4()),
                plan_id=plan.id if plan else None,  # type: ignore[union-attr]
                group_id=plan.group_id if plan else None,
                transfer_enable=plan.transfer_enable if plan else 0,
                device_limit=plan.device_limit if plan else None,
                speed_limit=plan.speed_limit if plan else None,
                expired_at=data.expired_at or 0,
            )
            user = await self.repo.create(user)
            generated.append(
                {
                    "id": user.id,
                    "email": email,
                    "password": password,
                    "uuid": user.uuid,
                    "token": user.token,
                }
            )
        return generated

    async def unbind_telegram(self, user_id: int) -> bool:
        """解绑 Telegram。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        user.telegram_id = None
        await self.repo.update(user)
        return True

    async def delete_user(self, user_id: int) -> None:
        """删除用户。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException(f"用户 {user_id} 不存在")
        await self._delete_user_related_data(user_id)
        await self.repo.delete(user)

    async def _delete_user_related_data(self, user_id: int) -> None:
        ticket_ids = (
            await self.repo.db.execute(select(Ticket.id).where(Ticket.user_id == user_id))
        ).scalars().all()
        if ticket_ids:
            await self.repo.db.execute(delete(TicketMessage).where(TicketMessage.ticket_id.in_(ticket_ids)))  # type: ignore[attr-defined]
        await self.repo.db.execute(delete(Ticket).where(Ticket.user_id == user_id))
        await self.repo.db.execute(delete(Order).where(Order.user_id == user_id))
        await self.repo.db.execute(delete(InviteCode).where(InviteCode.user_id == user_id))
        await self.repo.db.execute(update(User).where(User.invite_user_id == user_id).values(invite_user_id=None))


# ---- Entity → DTO 转换 ----
def _to_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,  # type: ignore[arg-type]
        email=user.email,
        is_admin=user.is_admin,
        is_staff=user.is_staff,
        banned=user.banned,
        plan_id=user.plan_id,
        created_at=user.created_at,
    )


def _to_read(user: User) -> UserRead:
    return UserRead.model_validate(user)


def _random_prefix(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
