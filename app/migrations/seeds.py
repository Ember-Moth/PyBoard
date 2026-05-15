"""迁移 seed 初始化。"""

import secrets
import time
import uuid

from sqlalchemy import Connection, MetaData, Table, select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.services.setting_defaults import DEFAULT_SETTINGS, serialize_setting_value
from app.utils.password import hash_password


def seed_default_settings_sync(connection: Connection, setting_table_name: str = "setting") -> int:
    """写入缺失的默认 settings，不覆盖已有配置。"""
    setting_table = _load_table(connection, setting_table_name)
    keys = [item.key for item in DEFAULT_SETTINGS]
    existing = set(
        connection.execute(select(setting_table.c.key).where(setting_table.c.key.in_(keys))).scalars().all()
    )
    now = int(time.time())
    rows = [
        {
            "key": item.key,
            "value": serialize_setting_value(item),
            "type": item.type,
            "description": item.description,
            "created_at": now,
            "updated_at": now,
        }
        for item in DEFAULT_SETTINGS
        if item.key not in existing
    ]
    if not rows:
        return 0
    connection.execute(setting_table.insert(), rows)
    return len(rows)


async def seed_default_settings(engine: AsyncEngine) -> int:
    """异步启动流程使用的 settings seed。"""
    async with engine.begin() as connection:
        return await connection.run_sync(seed_default_settings_sync)


def seed_initial_admin_sync(
    connection: Connection,
    email: str | None = None,
    password: str | None = None,
    user_table_name: str = "users",
) -> int:
    """创建初始管理员，不覆盖已有管理员或已有用户密码。"""
    user_table = _load_table(connection, user_table_name)
    admin_email = (email if email is not None else settings.initial_admin_email).strip().lower()
    admin_password = password if password is not None else settings.initial_admin_password
    if not admin_email or not admin_password:
        return 0

    existing_admin_id = connection.execute(
        select(user_table.c.id).where(user_table.c.is_admin.is_(True)).limit(1)
    ).scalar_one_or_none()
    if existing_admin_id is not None:
        return 0

    existing_user_id = connection.execute(
        select(user_table.c.id).where(user_table.c.email == admin_email)
    ).scalar_one_or_none()
    if existing_user_id is not None:
        connection.execute(
            user_table.update()
            .where(user_table.c.id == existing_user_id)
            .values(is_admin=True, is_staff=True)
        )
        return 1

    connection.execute(
        user_table.insert(),
        {
            "email": admin_email,
            "password": hash_password(admin_password),
            "token": secrets.token_hex(16),
            "invite_user_id": None,
            "telegram_id": None,
            "balance": 0,
            "discount": None,
            "commission_type": 0,
            "commission_rate": None,
            "commission_balance": 0,
            "t": 0,
            "u": 0,
            "d": 0,
            "transfer_enable": 0,
            "group_id": None,
            "plan_id": None,
            "speed_limit": None,
            "device_limit": None,
            "banned": False,
            "is_admin": True,
            "is_staff": True,
            "auto_renewal": 0,
            "remind_expire": 1,
            "remind_traffic": 1,
            "last_login_at": None,
            "last_login_ip": None,
            "uuid": str(uuid.uuid4()),
            "expired_at": 0,
            "remarks": "Initial administrator",
        },
    )
    return 1


async def seed_initial_admin(
    engine: AsyncEngine,
    email: str | None = None,
    password: str | None = None,
) -> int:
    """异步启动流程使用的初始管理员 seed。"""
    async with engine.begin() as connection:
        return await connection.run_sync(lambda sync_conn: seed_initial_admin_sync(sync_conn, email, password))


def _load_table(connection: Connection, table_name: str) -> Table:
    return Table(table_name, MetaData(), autoload_with=connection)
