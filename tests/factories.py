"""测试数据工厂 —— 简化测试中的模型构造。"""

import secrets
import time
import uuid

from app.models.user.entity import User
from app.utils.password import hash_password


def make_user(
    *,
    email: str | None = None,
    password: str = "password123",
    is_admin: bool = False,
    is_staff: bool = False,
    banned: bool = False,
) -> User:
    """构造一个有效的 User 实体（未持久化）。"""
    return User(
        email=email or f"user_{secrets.token_hex(4)}@test.local",
        password=hash_password(password),
        token=secrets.token_hex(16),
        uuid=str(uuid.uuid4()),
        is_admin=is_admin,
        is_staff=is_staff,
        banned=banned,
        last_login_at=int(time.time()),
    )
