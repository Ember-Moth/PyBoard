"""账户、公共配置和后台关键操作测试。"""

import hashlib
import urllib.parse

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.setting.entity import Setting
from app.models.user.entity import User


async def _set_setting(engine, key: str, value: str, type_: str = "str") -> None:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(Setting(key=key, value=value, type=type_))
        await db.commit()


@pytest.mark.asyncio
async def test_account_profile_password_and_quick_login(authed_client, client):
    res = await authed_client.get("/api/v1/user/info")
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "user@test.local"

    res = await authed_client.patch(
        "/api/v1/user/profile",
        json={"auto_renewal": 1, "remind_expire": 0},
    )
    assert res.status_code == 200
    assert res.json()["data"] is True

    res = await authed_client.post(
        "/api/v1/user/quick-login-url",
        json={"redirect": "dashboard"},
    )
    assert res.status_code == 200
    parsed = urllib.parse.urlparse(res.json()["data"])
    verify = urllib.parse.parse_qs(parsed.query or urllib.parse.urlparse(parsed.fragment).query)["verify"][0]
    res = await client.get(f"/api/v1/auth/token2-login?verify={verify}")
    assert res.status_code == 200
    assert res.json()["data"]["auth_token"].startswith("Bearer ")

    res = await authed_client.post(
        "/api/v1/user/change-password",
        json={"old_password": "password123", "new_password": "password456"},
    )
    assert res.status_code == 200
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.local", "password": "password456"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_email_verify_forget_and_comm_config(client, engine, cache):
    await _set_setting(engine, "app_url", "https://panel.example.com")
    await _set_setting(engine, "app_name", "Guest Panel")
    await _set_setting(engine, "app_description", "Guest panel description")
    await _set_setting(engine, "logo", "https://panel.example.com/logo.png")

    await client.post(
        "/api/v1/auth/register",
        json={"email": "forget@test.local", "password": "password123"},
    )

    res = await client.post(
        "/api/v1/auth/email-verify",
        json={"email": "forget@test.local", "isforget": 1},
    )
    assert res.status_code == 200
    code = await cache.get("email_verify_code:forget@test.local")
    assert code is not None

    res = await client.post(
        "/api/v1/auth/forget",
        json={"email": "forget@test.local", "email_code": str(code), "password": "new-password123"},
    )
    assert res.status_code == 200
    assert res.json()["data"] is True

    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "forget@test.local", "password": "new-password123"},
    )
    assert res.status_code == 200

    res = await client.get("/api/v1/common/config")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["logo"] == "https://panel.example.com/logo.png"
    assert data["stop_register"] == 0
    assert data["app_name"] == "Guest Panel"
    assert data["app_description"] == "Guest panel description"
    assert data["app_url"] == "https://panel.example.com"
    assert data["subscribe_url"] == ""
    assert data["subscribe_path"] == ""
    assert data["try_out_plan_id"] == 0
    assert data["try_out_hour"] == 1
    assert data["tos_url"] == ""
    assert data["currency"] == "CNY"
    assert data["currency_symbol"] == "¥"
    assert data["is_telegram"] == 0
    assert data["ticket_status"] == 0
    assert data["invite_gen_limit"] == 5
    assert data["withdraw_methods"] == ["alipay", "usdt", "bank"]
    assert data["withdraw_close"] == 0
    assert data["commission_withdraw_limit"] == 100


@pytest.mark.asyncio
async def test_admin_user_generate_ban_reset_and_invite(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/users/generate",
        json={"email_prefix": "generated", "email_suffix": "test.local", "password": "password123"},
    )
    assert res.status_code == 201
    user = res.json()["data"][0]

    res = await admin_client.post(f"/api/v1/admin/users/{user['id']}/ban", json={"banned": True})
    assert res.status_code == 200
    assert res.json()["data"] is True

    res = await admin_client.post(f"/api/v1/admin/users/{user['id']}/reset-security")
    assert res.status_code == 200
    assert res.json()["data"] is True

    res = await admin_client.post(
        f"/api/v1/admin/users/{user['id']}/invite-user",
        json={"invite_user_email": "admin@test.local"},
    )
    assert res.status_code == 200
    detail = await admin_client.get(f"/api/v1/admin/users/{user['id']}")
    assert detail.json()["data"]["invite_user_id"] is not None


@pytest.mark.asyncio
async def test_admin_order_assign_paid_cancel_and_update(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/plans",
        json={
            "name": "Admin Plan",
            "group_id": 1,
            "transfer_enable": 1024,
            "show": True,
            "month_price": 100,
        },
    )
    plan_id = res.json()["data"]["id"]

    res = await admin_client.post(
        "/api/v1/admin/orders/assign",
        json={"email": "admin@test.local", "plan_id": plan_id, "period": "month_price", "total_amount": 0},
    )
    assert res.status_code == 200
    trade_no = res.json()["data"]

    res = await admin_client.patch("/api/v1/admin/orders", json={"trade_no": trade_no, "commission_status": 3})
    assert res.status_code == 200

    res = await admin_client.post("/api/v1/admin/orders/paid", json={"trade_no": trade_no})
    assert res.status_code == 200
    assert res.json()["data"] is True

    me = await admin_client.get("/api/v1/auth/me")
    assert me.json()["data"]["plan_id"] == plan_id

    res = await admin_client.post(
        "/api/v1/admin/orders/assign",
        json={"email": "admin@test.local", "plan_id": plan_id, "period": "month_price", "total_amount": 0},
    )
    cancel_trade_no = res.json()["data"]
    res = await admin_client.post("/api/v1/admin/orders/cancel", json={"trade_no": cancel_trade_no})
    assert res.status_code == 200
    assert res.json()["data"] is True


@pytest.mark.asyncio
async def test_admin_setting_templates(admin_client):
    res = await admin_client.get("/api/v1/admin/settings/templates/email")
    assert res.status_code == 200
    assert "mail_verify.html" in res.json()["data"]

@pytest.mark.asyncio
async def test_staff_routes_require_staff_role(client, engine):
    token_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "staff@test.local", "password": "password123"},
    )
    token = token_res.json()["data"]["auth_token"]

    res = await client.get("/api/v1/staff/plans", headers={"Authorization": token})
    assert res.status_code == 403

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = (await db.execute(select(User).where(User.email == "staff@test.local"))).scalar_one()
        user.is_staff = True
        await db.commit()

    res = await client.get("/api/v1/staff/plans", headers={"Authorization": token})
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)


@pytest.mark.asyncio
async def test_telegram_webhook_bind_command(client, engine, monkeypatch):
    bot_token = "telegram-token"
    await _set_setting(engine, "telegram_bot_token", bot_token)
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "telegram@test.local", "password": "password123"},
    )
    assert register.status_code == 201

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = (await db.execute(select(User).where(User.email == "telegram@test.local"))).scalar_one()
        user_token = user.token

    calls = []

    class FakeResponse:
        def json(self):
            return {"ok": True, "result": {"username": "test_bot"}}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json):
            calls.append((url, json))
            return FakeResponse()

    monkeypatch.setattr("app.services.telegram.httpx.AsyncClient", FakeAsyncClient)
    access_token = hashlib.md5(bot_token.encode()).hexdigest()
    res = await client.post(
        f"/api/v1/telegram/webhook?access_token={access_token}",
        json={
            "update_id": 1,
            "message": {
                "text": f"/bind {user_token}",
                "chat": {"id": 12345, "type": "private"},
            },
        },
    )
    assert res.status_code == 200
    assert res.json()["data"] is True
    assert calls[-1][1]["text"] == "绑定成功"

    async with factory() as db:
        user = (await db.execute(select(User).where(User.email == "telegram@test.local"))).scalar_one()
        assert user.telegram_id == 12345
