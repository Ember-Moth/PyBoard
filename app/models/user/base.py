"""User 字段全集 —— 唯一真相源，不含 id/关系/系统字段。"""

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """所有业务字段定义在此，entity 和 dto 按需继承。"""

    # ---- 认证 ----
    email: str = Field(max_length=64, unique=True)
    password: str = Field(max_length=255)  # 扩容以容纳 Argon2id PHC
    token: str = Field(max_length=32, unique=True)

    # ---- 邀请 & 关联 ----
    invite_user_id: int | None = Field(default=None)
    telegram_id: int | None = None

    # ---- 余额 & 返佣 ----
    balance: int = 0
    discount: int | None = None
    commission_type: int = 0  # 0: system 1: period 2: onetime
    commission_rate: int | None = None
    commission_balance: int = 0

    # ---- 流量 ----
    t: int = Field(default=0, sa_type=BigInteger)
    u: int = Field(default=0, sa_type=BigInteger)
    d: int = Field(default=0, sa_type=BigInteger)
    transfer_enable: int = Field(default=0, sa_type=BigInteger)

    # ---- 套餐 & 限速 ----
    group_id: int | None = None
    plan_id: int | None = None
    speed_limit: int | None = None
    device_limit: int | None = None

    # ---- 状态 ----
    banned: bool = False
    is_admin: bool = False
    is_staff: bool = False
    auto_renewal: int = 0
    remind_expire: int = 1
    remind_traffic: int = 1

    # ---- 登录 ----
    last_login_at: int | None = None
    last_login_ip: int | None = None

    # ---- 其他 ----
    uuid: str = Field(max_length=36)
    expired_at: int = Field(default=0, sa_type=BigInteger)
    remarks: str | None = None
