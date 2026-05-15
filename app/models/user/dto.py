"""User DTO —— 接口视图，不做持久化。"""

from pydantic import AliasChoices, BaseModel, Field as PydanticField, field_validator
from sqlmodel import SQLModel


_TURNSTILE_TOKEN_ALIAS = AliasChoices("recaptcha_data", "turnstile_token", "cf-turnstile-response")


# ---- 认证 ----
class LoginRequest(BaseModel):
    """登录请求。"""

    email: str
    password: str
    recaptcha_data: str | None = PydanticField(default=None, validation_alias=_TURNSTILE_TOKEN_ALIAS)
    model_config = {"populate_by_name": True}

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("邮箱格式不正确")
        return value


class TokenResponse(BaseModel):
    """登录/注册返回的令牌。"""

    auth_token: str  # "Bearer eyJhbGciOi..."


class ForgetPasswordRequest(SQLModel):
    """忘记密码重置。"""

    email: str
    email_code: str
    password: str
    recaptcha_data: str | None = PydanticField(default=None, validation_alias=_TURNSTILE_TOKEN_ALIAS)
    model_config = {"populate_by_name": True}

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("邮箱格式不正确")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("密码长度至少 8 位")
        return value


class EmailVerifyRequest(SQLModel):
    """发送邮箱验证码。"""

    email: str
    isforget: int | None = None
    recaptcha_data: str | None = PydanticField(default=None, validation_alias=_TURNSTILE_TOKEN_ALIAS)
    model_config = {"populate_by_name": True}

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("邮箱格式不正确")
        return value


class UserChangePassword(SQLModel):
    """用户修改密码。"""

    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("密码长度至少 8 位")
        return value


class UserSelfUpdate(SQLModel):
    """用户可自行更新的偏好字段。"""

    auto_renewal: int | None = None
    remind_expire: int | None = None
    remind_traffic: int | None = None


# ---- 创建 ----
class UserCreate(SQLModel):
    """注册/创建用户。"""

    email: str
    password: str
    invite_code: str | None = None
    email_code: str | None = None
    recaptcha_data: str | None = PydanticField(default=None, validation_alias=_TURNSTILE_TOKEN_ALIAS)
    model_config = {"populate_by_name": True}

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("邮箱格式不正确")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("密码长度至少 8 位")
        return value


# ---- 更新 ----
class UserUpdate(SQLModel):
    """部分更新，所有字段 Optional。"""

    email: str | None = None
    password: str | None = None
    balance: int | None = None
    discount: int | None = None
    commission_type: int | None = None
    commission_rate: int | None = None
    transfer_enable: int | None = None
    device_limit: int | None = None
    banned: bool | None = None
    is_admin: bool | None = None
    is_staff: bool | None = None
    speed_limit: int | None = None
    group_id: int | None = None
    plan_id: int | None = None
    auto_renewal: int | None = None
    remind_expire: int | None = None
    remind_traffic: int | None = None
    expired_at: int | None = None
    remarks: str | None = None


class AdminUserGenerate(SQLModel):
    """管理端生成用户。"""

    email_prefix: str | None = None
    email_suffix: str
    password: str | None = None
    plan_id: int | None = None
    expired_at: int | None = None
    generate_count: int | None = None


class AdminUserBan(SQLModel):
    """管理端封禁/解封用户。"""

    banned: bool = True


class AdminUserInviteSetter(SQLModel):
    """管理端设置邀请人。"""

    invite_user_email: str | None = None


# ---- 列表 ----
class UserPublic(SQLModel):
    """公开列表展示（脱敏）。"""

    id: int
    email: str
    is_admin: bool
    is_staff: bool
    banned: bool
    plan_id: int | None
    created_at: int


# ---- 详情 ----
class UserRead(SQLModel):
    """管理端详情，不含密码/token 等敏感字段。"""

    id: int
    email: str
    invite_user_id: int | None = None
    telegram_id: int | None = None
    balance: int
    discount: int | None = None
    commission_type: int
    commission_rate: int | None = None
    commission_balance: int
    t: int
    u: int
    d: int
    transfer_enable: int
    device_limit: int | None = None
    banned: bool
    is_admin: bool
    is_staff: bool
    last_login_at: int | None = None
    last_login_ip: int | None = None
    uuid: str
    group_id: int | None = None
    plan_id: int | None = None
    speed_limit: int | None = None
    auto_renewal: int
    remind_expire: int
    remind_traffic: int
    expired_at: int
    remarks: str | None = None
    created_at: int
    updated_at: int
