"""认证流程集成测试 —— 注册 → 登录 → /api/v1/auth/me。"""

import pytest


@pytest.mark.asyncio
async def test_register_then_login_then_me(client):
    payload = {"email": "alice@test.local", "password": "password123"}

    # 注册
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["code"] == 201
    token = body["data"]["auth_token"]
    assert token.startswith("Bearer ")

    # 登录
    res = await client.post("/api/v1/auth/login", json=payload)
    assert res.status_code == 200
    assert res.json()["data"]["auth_token"].startswith("Bearer ")

    # 获取当前用户
    res = await client.get("/api/v1/auth/me", headers={"Authorization": token})
    assert res.status_code == 200
    me = res.json()["data"]
    assert me["email"] == payload["email"]


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(client):
    payload = {"email": "dup@test.local", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)

    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409
    assert res.json()["code"] == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@test.local", "password": "password123"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@test.local", "password": "wrong-password"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_unauthorized(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
