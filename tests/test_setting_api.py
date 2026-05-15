"""Setting API 集成测试。"""

import pytest


def _setting_payload(key: str = "test_key", value: str = "test_value") -> dict:
    return {
        "key": key,
        "value": value,
        "type": "str",
        "description": "Test setting",
    }


# ---- 权限控制 ----
@pytest.mark.asyncio
async def test_setting_requires_token(client):
    res = await client.get("/api/v1/admin/settings")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_setting_rejects_normal_user(authed_client):
    res = await authed_client.get("/api/v1/admin/settings")
    assert res.status_code == 403


# ---- CRUD ----
@pytest.mark.asyncio
async def test_admin_create_setting(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/settings", json=_setting_payload("site_name", "Test Panel")
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["key"] == "site_name"
    assert data["value"] == "Test Panel"


@pytest.mark.asyncio
async def test_admin_list_settings(admin_client):
    await admin_client.post("/api/v1/admin/settings", json=_setting_payload("k1", "v1"))
    await admin_client.post("/api/v1/admin/settings", json=_setting_payload("k2", "v2"))

    res = await admin_client.get("/api/v1/admin/settings")
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 2
    # Public 视图不含 value
    assert "value" not in items[0]


@pytest.mark.asyncio
async def test_admin_get_setting_detail(admin_client):
    res = await admin_client.post("/api/v1/admin/settings", json=_setting_payload("k", "v"))
    sid = res.json()["data"]["id"]

    res = await admin_client.get(f"/api/v1/admin/settings/{sid}")
    assert res.status_code == 200
    # Read 视图含 value
    assert res.json()["data"]["value"] == "v"


@pytest.mark.asyncio
async def test_admin_update_setting(admin_client):
    res = await admin_client.post("/api/v1/admin/settings", json=_setting_payload("k", "old"))
    sid = res.json()["data"]["id"]

    res = await admin_client.patch(
        f"/api/v1/admin/settings/{sid}", json={"value": "new", "description": "updated"}
    )
    assert res.status_code == 200
    assert res.json()["data"]["value"] == "new"
    assert res.json()["data"]["description"] == "updated"


@pytest.mark.asyncio
async def test_admin_delete_setting(admin_client):
    res = await admin_client.post("/api/v1/admin/settings", json=_setting_payload("del", "me"))
    sid = res.json()["data"]["id"]

    res = await admin_client.delete(f"/api/v1/admin/settings/{sid}")
    assert res.status_code == 204

    res = await admin_client.get(f"/api/v1/admin/settings/{sid}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_key_conflict(admin_client):
    await admin_client.post("/api/v1/admin/settings", json=_setting_payload("dup", "v1"))
    res = await admin_client.post("/api/v1/admin/settings", json=_setting_payload("dup", "v2"))
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_get_missing_setting_404(admin_client):
    res = await admin_client.get("/api/v1/admin/settings/9999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_admin_setting_groups_routes(admin_client):
    res = await admin_client.put(
        "/api/v1/admin/settings/values",
        json={"key": "app_name", "value": "Test App"},
    )
    assert res.status_code == 200

    res = await admin_client.get("/api/v1/admin/settings/groups/site")
    assert res.status_code == 200
    assert res.json()["data"]["site"]["app_name"] == "Test App"
