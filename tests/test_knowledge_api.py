"""Knowledge API 集成测试。"""

import pytest


def _payload(
    title: str = "title",
    *,
    language: str = "zh-CN",
    category: str = "general",
    body: str = "body content",
    show: bool = True,
    sort: int | None = None,
) -> dict:
    return {
        "title": title,
        "language": language,
        "category": category,
        "body": body,
        "show": show,
        "sort": sort,
    }


# ---- 用户端 ----
@pytest.mark.asyncio
async def test_user_list_grouped_by_category(client, admin_client):
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("a", category="usage"))
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("b", category="usage"))
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("c", category="faq"))

    res = await client.get("/api/v1/knowledge")
    assert res.status_code == 200
    data = res.json()["data"]
    assert set(data.keys()) == {"usage", "faq"}
    assert len(data["usage"]) == 2
    assert len(data["faq"]) == 1
    # 用户端字段不含 body
    assert "body" not in data["faq"][0]


@pytest.mark.asyncio
async def test_user_list_excludes_hidden(client, admin_client):
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("v", show=True))
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("h", show=False))

    res = await client.get("/api/v1/knowledge")
    flattened = [item for arr in res.json()["data"].values() for item in arr]
    titles = [k["title"] for k in flattened]
    assert titles == ["v"]


@pytest.mark.asyncio
async def test_user_list_filter_by_language(client, admin_client):
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("cn", language="zh-CN"))
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("en", language="en-US"))

    res = await client.get("/api/v1/knowledge?language=en-US")
    flattened = [item for arr in res.json()["data"].values() for item in arr]
    assert [k["title"] for k in flattened] == ["en"]


@pytest.mark.asyncio
async def test_user_list_keyword(client, admin_client):
    await admin_client.post(
        "/api/v1/admin/knowledge",
        json=_payload("hello", body="x"),
    )
    await admin_client.post(
        "/api/v1/admin/knowledge",
        json=_payload("other", body="contains hello"),
    )
    await admin_client.post(
        "/api/v1/admin/knowledge",
        json=_payload("nope", body="irrelevant"),
    )

    res = await client.get("/api/v1/knowledge?keyword=hello")
    flattened = [item for arr in res.json()["data"].values() for item in arr]
    titles = {k["title"] for k in flattened}
    assert titles == {"hello", "other"}


@pytest.mark.asyncio
async def test_user_get_visible(client, admin_client):
    res = await admin_client.post(
        "/api/v1/admin/knowledge",
        json=_payload("t", body="hi"),
    )
    kid = res.json()["data"]["id"]

    res = await client.get(f"/api/v1/knowledge/{kid}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["title"] == "t"
    assert data["body"] == "hi"


@pytest.mark.asyncio
async def test_user_get_hidden_404(client, admin_client):
    res = await admin_client.post(
        "/api/v1/admin/knowledge",
        json=_payload("h", show=False),
    )
    kid = res.json()["data"]["id"]

    res = await client.get(f"/api/v1/knowledge/{kid}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_user_languages(client, admin_client):
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("a", language="zh-CN"))
    await admin_client.post("/api/v1/admin/knowledge", json=_payload("b", language="en-US"))
    await admin_client.post(
        "/api/v1/admin/knowledge", json=_payload("h", language="ja-JP", show=False)
    )

    res = await client.get("/api/v1/knowledge/languages")
    assert res.status_code == 200
    assert res.json()["data"] == ["en-US", "zh-CN"]


# ---- 管理端鉴权 ----
@pytest.mark.asyncio
async def test_admin_requires_token(client):
    res = await client.get("/api/v1/admin/knowledge")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_rejects_normal_user(authed_client):
    res = await authed_client.get("/api/v1/admin/knowledge")
    assert res.status_code == 403


# ---- 管理端 CRUD ----
@pytest.mark.asyncio
async def test_admin_crud_flow(admin_client):
    # 创建
    res = await admin_client.post(
        "/api/v1/admin/knowledge",
        json=_payload("draft", show=False, sort=10),
    )
    assert res.status_code == 201
    kid = res.json()["data"]["id"]

    # 列表（含未上线）
    res = await admin_client.get("/api/v1/admin/knowledge")
    data = res.json()["data"]
    assert data["total"] == 1

    # 详情
    res = await admin_client.get(f"/api/v1/admin/knowledge/{kid}")
    assert res.json()["data"]["show"] is False

    # 更新
    res = await admin_client.patch(
        f"/api/v1/admin/knowledge/{kid}",
        json={"show": True, "title": "published"},
    )
    body = res.json()["data"]
    assert body["show"] is True
    assert body["title"] == "published"

    # 删除
    res = await admin_client.delete(f"/api/v1/admin/knowledge/{kid}")
    assert res.status_code == 204

    res = await admin_client.get(f"/api/v1/admin/knowledge/{kid}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_missing_404(admin_client):
    res = await admin_client.patch("/api/v1/admin/knowledge/9999", json={"title": "x"})
    assert res.status_code == 404
