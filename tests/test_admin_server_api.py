"""管理端节点模块测试。"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_server_group_route_and_node_flow(admin_client: AsyncClient):
    group_res = await admin_client.post("/api/v1/admin/servers/groups", json={"name": "default"})
    assert group_res.status_code == 201
    group_id = group_res.json()["data"]["id"]

    route_res = await admin_client.post(
        "/api/v1/admin/servers/routes",
        json={
            "remarks": "block example",
            "match": ["domain:example.com"],
            "action": "block",
        },
    )
    assert route_res.status_code == 201
    route_id = route_res.json()["data"]["id"]

    node_payload = {
        "group_id": [group_id],
        "route_id": [route_id],
        "name": "node-1",
        "host": "node.example.com",
        "port": "443",
        "server_port": 443,
        "rate": "1",
        "protocol": "vless",
        "tls": 1,
        "network": "tcp",
        "tls_settings": {"server_name": "example.com"},
        "network_settings": {"path": "/ws"},
        "show": True,
    }
    node_res = await admin_client.post("/api/v1/admin/servers/nodes", json=node_payload)
    assert node_res.status_code == 201
    node = node_res.json()["data"]
    node_id = node["id"]
    assert node["group_id"] == [group_id]
    assert node["route_id"] == [route_id]
    assert node["tls_settings"] == {"server_name": "example.com"}

    res = await admin_client.get("/api/v1/admin/servers/groups")
    assert res.status_code == 200
    group = res.json()["data"][0]
    assert group["server_count"] == 1

    res = await admin_client.get("/api/v1/admin/servers/routes")
    assert res.status_code == 200
    assert res.json()["data"][0]["match"] == ["domain:example.com"]

    res = await admin_client.patch(f"/api/v1/admin/servers/nodes/{node_id}", json={"show": False, "sort": 9})
    assert res.status_code == 200
    assert res.json()["data"]["show"] is False
    assert res.json()["data"]["sort"] == 9

    res = await admin_client.post(f"/api/v1/admin/servers/nodes/{node_id}/copy")
    assert res.status_code == 200
    copied = res.json()["data"]
    assert copied["id"] != node_id
    assert copied["show"] is False

    res = await admin_client.post("/api/v1/admin/servers/nodes/sort", json={str(node_id): 3})
    assert res.status_code == 200
    assert res.json()["data"] is True

    res = await admin_client.delete(f"/api/v1/admin/servers/routes/{route_id}")
    assert res.status_code == 409

    res = await admin_client.delete(f"/api/v1/admin/servers/groups/{group_id}")
    assert res.status_code == 409

    await admin_client.delete(f"/api/v1/admin/servers/nodes/{node_id}")
    await admin_client.delete(f"/api/v1/admin/servers/nodes/{copied['id']}")
    res = await admin_client.delete(f"/api/v1/admin/servers/routes/{route_id}")
    assert res.status_code == 204
    res = await admin_client.delete(f"/api/v1/admin/servers/groups/{group_id}")
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_admin_server_node_rejects_invalid_json_settings(admin_client: AsyncClient):
    group_res = await admin_client.post("/api/v1/admin/servers/groups", json={"name": "json-check"})
    assert group_res.status_code == 201
    group_id = group_res.json()["data"]["id"]

    node_payload = {
        "group_id": [group_id],
        "name": "bad-json-node",
        "host": "node.example.com",
        "port": "443",
        "server_port": 443,
        "rate": "1",
        "protocol": "vless",
        "tls": 1,
        "network": "tcp",
        "tls_settings": "{bad-json",
        "show": True,
    }
    res = await admin_client.post("/api/v1/admin/servers/nodes", json=node_payload)
    assert res.status_code == 400
    assert "JSON 对象" in res.json()["msg"]
