"""User 管理端 API 鉴权测试。"""

import pytest


@pytest.mark.asyncio
async def test_admin_users_requires_token(client):
    res = await client.get("/api/v1/admin/users")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_users_rejects_normal_user(authed_client):
    res = await authed_client.get("/api/v1/admin/users")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_users_list(admin_client):
    res = await admin_client.get("/api/v1/admin/users")
    assert res.status_code == 200
    assert res.json()["code"] == 200
