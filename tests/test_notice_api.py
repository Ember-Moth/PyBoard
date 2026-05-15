"""Notice API 集成测试 —— 覆盖用户端 + 管理端。"""

import pytest


# ---- 用户端 ----
@pytest.mark.asyncio
async def test_user_list_only_returns_visible(client, admin_client):
    # 用 admin_client 创建两条公告：一条 show，一条隐藏
    await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "v1", "content": "c1", "show": True},
    )
    await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "h1", "content": "c2", "show": False},
    )

    res = await client.get("/api/v1/notices")
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["size"] == 10
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["title"] == "v1"
    # 公开视图不应包含 content / show / updated_at
    assert "content" not in item
    assert "show" not in item


@pytest.mark.asyncio
async def test_user_get_visible_notice(client, admin_client):
    res = await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "hello", "content": "world", "show": True},
    )
    notice_id = res.json()["data"]["id"]

    res = await client.get(f"/api/v1/notices/{notice_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["title"] == "hello"
    assert data["content"] == "world"


@pytest.mark.asyncio
async def test_user_get_hidden_notice_returns_404(client, admin_client):
    res = await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "secret", "content": "...", "show": False},
    )
    notice_id = res.json()["data"]["id"]

    res = await client.get(f"/api/v1/notices/{notice_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_user_get_missing_notice_returns_404(client):
    res = await client.get("/api/v1/notices/9999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_user_pagination_params(client, admin_client):
    for i in range(15):
        await admin_client.post(
            "/api/v1/admin/notices",
            json={"title": f"n{i}", "content": "x", "show": True},
        )

    res = await client.get("/api/v1/notices?page=2&size=10")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 15
    assert data["page"] == 2
    assert data["size"] == 10
    assert len(data["items"]) == 5


# ---- 管理端鉴权 ----
@pytest.mark.asyncio
async def test_admin_endpoints_require_token(client):
    res = await client.get("/api/v1/admin/notices")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoints_reject_normal_user(authed_client):
    res = await authed_client.get("/api/v1/admin/notices")
    assert res.status_code == 403


# ---- 管理端 CRUD ----
@pytest.mark.asyncio
async def test_admin_create_notice(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "标题",
            "content": "内容",
            "show": True,
            "tags": "公告,系统",
        },
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["title"] == "标题"
    assert data["show"] is True
    assert data["created_at"] > 0
    assert data["updated_at"] > 0


@pytest.mark.asyncio
async def test_admin_list_includes_hidden(admin_client):
    await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "v", "content": "c", "show": True},
    )
    await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "h", "content": "c", "show": False},
    )
    res = await admin_client.get("/api/v1/admin/notices")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_admin_update_notice(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "old", "content": "x", "show": False},
    )
    notice_id = res.json()["data"]["id"]

    res = await admin_client.patch(
        f"/api/v1/admin/notices/{notice_id}",
        json={"title": "new", "show": True},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["title"] == "new"
    assert data["show"] is True
    # 未更新的字段保持
    assert data["content"] == "x"


@pytest.mark.asyncio
async def test_admin_delete_notice(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/notices",
        json={"title": "del", "content": "x", "show": True},
    )
    notice_id = res.json()["data"]["id"]

    res = await admin_client.delete(f"/api/v1/admin/notices/{notice_id}")
    assert res.status_code == 204

    res = await admin_client.get(f"/api/v1/admin/notices/{notice_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_missing_returns_404(admin_client):
    res = await admin_client.patch("/api/v1/admin/notices/9999", json={"title": "x"})
    assert res.status_code == 404
