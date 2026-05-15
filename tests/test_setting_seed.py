"""Setting seed 测试。"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select

from app.migrations.seeds import seed_default_settings, seed_initial_admin
from app.models.setting.entity import Setting
from app.models.user.entity import User
from app.utils.password import hash_password, verify_and_upgrade


@pytest.mark.asyncio
async def test_seed_default_settings_inserts_missing_items(engine):
    inserted = await seed_default_settings(engine)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        result = await db.execute(select(Setting).where(Setting.key == "app_name"))
        app_name = result.scalar_one()

        result = await db.execute(select(Setting).where(Setting.key == "email_whitelist_suffix"))
        whitelist = result.scalar_one()

    assert inserted > 0
    assert app_name.value == "PyBoard"
    assert app_name.type == "str"
    assert app_name.description == "应用名称"
    assert whitelist.type == "json"
    assert "gmail.com" in whitelist.value


@pytest.mark.asyncio
async def test_seed_default_settings_is_idempotent_and_keeps_existing_values(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        db.add(Setting(key="app_name", value="Custom Panel", type="str", description="custom"))
        await db.commit()

    first_inserted = await seed_default_settings(engine)
    second_inserted = await seed_default_settings(engine)

    async with factory() as db:
        result = await db.execute(select(Setting).where(Setting.key == "app_name"))
        app_name = result.scalar_one()

    assert first_inserted > 0
    assert second_inserted == 0
    assert app_name.value == "Custom Panel"
    assert app_name.description == "custom"


@pytest.mark.asyncio
async def test_seed_initial_admin_creates_admin_when_configured(engine):
    created = await seed_initial_admin(engine, "OWNER@Test.Local", "password123")
    second_created = await seed_initial_admin(engine, "other@test.local", "password456")

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        result = await db.execute(select(User).where(User.email == "owner@test.local"))
        admin = result.scalar_one()
        admins = (await db.execute(select(User).where(User.is_admin.is_(True)))).scalars().all()  # type: ignore[attr-defined]

    valid, _new_hash = verify_and_upgrade("password123", admin.password)
    assert created == 1
    assert second_created == 0
    assert valid
    assert admin.is_admin is True
    assert admin.is_staff is True
    assert len(admins) == 1


@pytest.mark.asyncio
async def test_seed_initial_admin_promotes_existing_user_without_resetting_password(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    original_hash = hash_password("old-password")
    async with factory() as db:
        db.add(
            User(
                email="existing@test.local",
                password=original_hash,
                token="a" * 32,
                uuid="00000000-0000-0000-0000-000000000001",
            )
        )
        await db.commit()

    promoted = await seed_initial_admin(engine, "existing@test.local", "new-password")

    async with factory() as db:
        result = await db.execute(select(User).where(User.email == "existing@test.local"))
        user = result.scalar_one()

    old_valid, _old_new_hash = verify_and_upgrade("old-password", user.password)
    new_valid, _new_new_hash = verify_and_upgrade("new-password", user.password)
    assert promoted == 1
    assert user.is_admin is True
    assert user.is_staff is True
    assert old_valid
    assert not new_valid


@pytest.mark.asyncio
async def test_seed_initial_admin_skips_when_credentials_are_incomplete(engine):
    assert await seed_initial_admin(engine, "", "password123") == 0
    assert await seed_initial_admin(engine, "admin@test.local", "") == 0

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        users = (await db.execute(select(User))).scalars().all()

    assert users == []
