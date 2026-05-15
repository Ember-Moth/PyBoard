"""认证服务 —— 用户注册、登录、JWT 签发与解析。"""

import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.cache import RuntimeCache
from app.core.config import settings
from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException, UnauthorizedException
from app.models.user.dto import EmailVerifyRequest, ForgetPasswordRequest, LoginRequest, TokenResponse, UserCreate, UserRead
from app.models.user.entity import User
from app.repositories.invite_code import InviteCodeRepository
from app.repositories.user import UserRepository
from app.services.setting import SettingService
from app.utils.password import hash_password, verify_and_upgrade

_EMAIL_VERIFY_CODE_PREFIX = "email_verify_code:"
_EMAIL_VERIFY_LAST_SEND_PREFIX = "email_verify_last_send:"
_EMAIL_VERIFY_RATE_PREFIX = "email_verify_rate:"


class AuthService:
    """认证业务逻辑。"""

    def __init__(
        self,
        repo: UserRepository,
        setting_service: SettingService,
        invite_repo: InviteCodeRepository,
        cache: RuntimeCache,
    ):
        self.repo = repo
        self.setting_service = setting_service
        self.invite_repo = invite_repo
        self.cache = cache

    async def register(self, data: UserCreate, client_ip: str | None = None) -> TokenResponse:
        """注册用户并签发访问令牌。"""
        if await self.setting_service.get_int("stop_register", 0):
            raise ForbiddenException("当前停止注册")
        await self._check_email_policy(data.email)
        await self._check_register_limit(client_ip)
        if await self.setting_service.get_int("email_verify", 0):
            await self._verify_email_code(data.email, data.email_code)
        if await self.repo.email_exists(data.email):
            raise ConflictException("邮箱已注册")

        invite_user_id = await self._resolve_invite_user_id(data.invite_code)
        user = User(
            email=data.email,
            password=hash_password(data.password),
            token=secrets.token_hex(16),
            uuid=str(uuid.uuid4()),
            invite_user_id=invite_user_id,
            last_login_at=int(time.time()),
        )
        user = await self.repo.create(user)
        await self.cache.delete(f"{_EMAIL_VERIFY_CODE_PREFIX}{data.email}")
        return self._build_auth_token(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """验证邮箱密码并签发访问令牌。"""
        user = await self.repo.get_by_email(data.email)
        if user is None:
            raise UnauthorizedException("邮箱或密码错误")

        valid, new_hash = verify_and_upgrade(data.password, user.password)
        if not valid:
            raise UnauthorizedException("邮箱或密码错误")
        if user.banned:
            raise ForbiddenException("账号已被封禁")

        if new_hash is not None:
            user.password = new_hash
        user.last_login_at = int(time.time())
        user = await self.repo.update(user)
        return self._build_auth_token(user)

    async def get_current_user(self, token: str) -> UserRead:
        """解析 JWT 并返回当前用户。"""
        user_id = self._decode_user_id(token)
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException()
        if user.banned:
            raise ForbiddenException("账号已被封禁")
        return _to_read(user)

    async def build_token_for_user_id(self, user_id: int) -> TokenResponse:
        """为指定用户签发访问令牌。"""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException()
        if user.banned:
            raise ForbiddenException("账号已被封禁")
        user.last_login_at = int(time.time())
        user = await self.repo.update(user)
        return self._build_auth_token(user)

    async def forget_password(self, data: ForgetPasswordRequest, email_code: str | None = None) -> bool:
        """通过邮箱验证码重置密码。"""
        email_code = email_code if email_code is not None else await self.cache.get(f"{_EMAIL_VERIFY_CODE_PREFIX}{data.email}")
        if not email_code or str(email_code) != str(data.email_code):
            raise BadRequestException("邮箱验证码错误")
        user = await self.repo.get_by_email(data.email)
        if user is None:
            raise NotFoundException("该邮箱未注册")
        user.password = hash_password(data.password)
        await self.repo.update(user)
        await self.cache.delete(f"{_EMAIL_VERIFY_CODE_PREFIX}{data.email}")
        return True

    async def create_email_verify_code(self, data: EmailVerifyRequest, client_ip: str | None = None) -> str:
        """创建邮箱验证码并写入运行期缓存。"""
        await self._check_email_verify_rate(client_ip)
        await self._check_email_policy(data.email)

        exists = await self.repo.email_exists(data.email)
        if data.isforget == 0 and exists:
            raise ConflictException("该邮箱已注册")
        if data.isforget == 1 and not exists:
            raise NotFoundException("该邮箱未注册")

        if await self.cache.get(f"{_EMAIL_VERIFY_LAST_SEND_PREFIX}{data.email}"):
            raise BadRequestException("邮箱验证码已发送，请稍后再试")

        code = f"{secrets.randbelow(900000) + 100000}"
        await self.cache.set(f"{_EMAIL_VERIFY_CODE_PREFIX}{data.email}", code, ex=300)
        await self.cache.set(f"{_EMAIL_VERIFY_LAST_SEND_PREFIX}{data.email}", int(time.time()), ex=60)
        return code

    async def require_admin(self, token: str) -> UserRead:
        """解析 JWT 并要求管理员权限。"""
        user = await self.get_current_user(token)
        if not user.is_admin:
            raise ForbiddenException()
        return user

    async def require_staff(self, token: str) -> UserRead:
        """解析 JWT 并要求员工或管理员权限。"""
        user = await self.get_current_user(token)
        if not user.is_staff and not user.is_admin:
            raise ForbiddenException()
        return user

    def _build_auth_token(self, user: User) -> TokenResponse:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        expires_at = datetime.now(UTC) + expires_delta
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin,
            "is_staff": user.is_staff,
            "iat": datetime.now(UTC),
            "exp": expires_at,
        }
        access_token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return TokenResponse(
            auth_token=f"Bearer {access_token}",
        )

    def _decode_user_id(self, token: str) -> int:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            subject = payload.get("sub")
            if subject is None:
                raise UnauthorizedException()
            return int(subject)
        except (JWTError, ValueError):
            raise UnauthorizedException() from None

    async def _resolve_invite_user_id(self, invite_code: str | None) -> int | None:
        invite_force = await self.setting_service.get_int("invite_force", 0)
        if not invite_code:
            if invite_force:
                raise BadRequestException("请填写邀请码")
            return None
        invite = await self.invite_repo.get_active_by_code(invite_code.strip().upper())
        if invite is None:
            raise BadRequestException("邀请码无效")
        invite.pv += 1
        if not await self.setting_service.get_int("invite_never_expire", 0):
            invite.status = 1
        await self.invite_repo.update(invite)
        return invite.user_id

    async def record_invite_pv(self, invite_code: str | None) -> bool:
        """记录邀请码访问次数。"""
        if not invite_code:
            return True
        invite = await self.invite_repo.get_by_code(invite_code.strip().upper())
        if invite:
            invite.pv += 1
            await self.invite_repo.update(invite)
        return True

    async def _check_email_policy(self, email: str) -> None:
        if await self.setting_service.get_int("email_whitelist_enable", 0):
            suffixes = await self.setting_service.get_json("email_whitelist_suffix", [])
            domain = email.rsplit("@", 1)[-1].lower()
            allowed = {str(item).lower().lstrip("@") for item in suffixes}
            if domain not in allowed:
                raise BadRequestException("当前邮箱后缀不允许注册")
        if await self.setting_service.get_int("email_gmail_limit_enable", 0):
            local, _, domain = email.partition("@")
            if domain.lower() == "gmail.com" and ("+" in local or "." in local):
                raise BadRequestException("当前 Gmail 邮箱格式不允许注册")

    async def _check_register_limit(self, client_ip: str | None) -> None:
        if not client_ip or not await self.setting_service.get_int("register_limit_by_ip_enable", 0):
            return
        count = await self.setting_service.get_int("register_limit_count", 3)
        expire = await self.setting_service.get_int("register_limit_expire", 60)
        key = f"register_limit:{client_ip}"
        current = await self.cache.incr(key, ex=expire)
        if current > count:
            raise BadRequestException("该 IP 注册过于频繁")

    async def _check_email_verify_rate(self, client_ip: str | None) -> None:
        if not client_ip:
            return
        key = f"{_EMAIL_VERIFY_RATE_PREFIX}{client_ip}"
        current = await self.cache.incr(key, ex=60)
        if current > 3:
            raise BadRequestException("请求过于频繁，请稍后再试")

    async def _verify_email_code(self, email: str, email_code: str | None) -> None:
        if not email_code:
            raise BadRequestException("邮箱验证码不能为空")
        code = await self.cache.get(f"{_EMAIL_VERIFY_CODE_PREFIX}{email}")
        if str(code) != str(email_code):
            raise BadRequestException("邮箱验证码错误")


def _to_read(user: User) -> UserRead:
    return UserRead.model_validate(user)
