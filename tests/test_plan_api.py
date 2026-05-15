"""Plan API 集成测试。"""

import pytest


def _plan_payload(
    name: str = "Basic", *, show: bool = True, renew: bool = True, capacity_limit: int | None = None
) -> dict:
    return {
        "name": name,
        "group_id": 1,
        "transfer_enable": 10 * 1024**3,  # 10 GB
        "show": show,
        "renew": renew,
        "capacity_limit": capacity_limit,
    }


# ---- 用户端列表 ----
@pytest.mark.asyncio
async def test_user_list_returns_only_visible(client, admin_client):
    await admin_client.post("/api/v1/admin/plans", json=_plan_payload("Vip", show=True))
    await admin_client.post("/api/v1/admin/plans", json=_plan_payload("Hidden", show=False))

    res = await client.get("/api/v1/plans")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["data"]]
    assert names == ["Vip"]


@pytest.mark.asyncio
async def test_capacity_remaining(client, admin_client):
    # 创建容量限制为 2 的套餐
    await admin_client.post(
        "/api/v1/admin/plans", json=_plan_payload("Limited", show=True, capacity_limit=2)
    )

    # 检查容量剩余 2（0 活跃用户）
    res = await client.get("/api/v1/plans")
    plans = res.json()["data"]
    assert plans[0]["capacity_limit"] == 2


# ---- 用户端详情：隐藏但可续费 ----
@pytest.mark.asyncio
async def test_hidden_renewable_plan_404_for_non_owner(authed_client, admin_client):
    # 创建隐藏但可续费的套餐
    res = await admin_client.post(
        "/api/v1/admin/plans", json=_plan_payload("HiddenPlan", show=False, renew=True)
    )
    plan_id = res.json()["data"]["id"]

    # 测试当前用户不持有，应该 404
    res = await authed_client.get(f"/api/v1/plans/{plan_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_hidden_non_renewable_404(client, admin_client):
    # 创建隐藏且不可续费的套餐
    res = await admin_client.post(
        "/api/v1/admin/plans", json=_plan_payload("DeadPlan", show=False, renew=False)
    )
    plan_id = res.json()["data"]["id"]

    res = await client.get(f"/api/v1/plans/{plan_id}")
    assert res.status_code == 404


# ---- 管理端鉴权 ----
@pytest.mark.asyncio
async def test_admin_requires_token(client):
    res = await client.get("/api/v1/admin/plans")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_rejects_normal_user(authed_client):
    res = await authed_client.get("/api/v1/admin/plans")
    assert res.status_code == 403


# ---- 管理端 CRUD ----
@pytest.mark.asyncio
async def test_admin_create_plan(admin_client):
    res = await admin_client.post("/api/v1/admin/plans", json=_plan_payload("NewPlan"))
    assert res.status_code == 201
    assert res.json()["data"]["name"] == "NewPlan"


@pytest.mark.asyncio
async def test_admin_list_includes_hidden(admin_client):
    await admin_client.post("/api/v1/admin/plans", json=_plan_payload("Show", show=True))
    await admin_client.post("/api/v1/admin/plans", json=_plan_payload("Hide", show=False))

    res = await admin_client.get("/api/v1/admin/plans")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["data"]]
    assert set(names) == {"Show", "Hide"}


@pytest.mark.asyncio
async def test_admin_list_has_count_field(admin_client):
    """管理端列表应包含 count（活跃用户数）字段"""
    await admin_client.post("/api/v1/admin/plans", json=_plan_payload("Test"))

    res = await admin_client.get("/api/v1/admin/plans")
    plans = res.json()["data"]
    assert "count" in plans[0]
    # 新建套餐 count = 0
    assert plans[0]["count"] == 0


@pytest.mark.asyncio
async def test_admin_update_plan(admin_client):
    res = await admin_client.post("/api/v1/admin/plans", json=_plan_payload("OldName"))
    plan_id = res.json()["data"]["id"]

    res = await admin_client.patch(
        f"/api/v1/admin/plans/{plan_id}", json={"name": "NewName", "show": False}
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "NewName"
    assert res.json()["data"]["show"] is False


@pytest.mark.asyncio
async def test_admin_delete_empty_plan(admin_client):
    res = await admin_client.post("/api/v1/admin/plans", json=_plan_payload("ToDelete"))
    plan_id = res.json()["data"]["id"]

    res = await admin_client.delete(f"/api/v1/admin/plans/{plan_id}")
    assert res.status_code == 204

    res = await admin_client.get(f"/api/v1/admin/plans/{plan_id}")
    assert res.status_code == 404
