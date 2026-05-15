"""V2Node 服务端配置接口测试。"""

import base64
import hashlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.server_route.entity import ServerRoute
from app.models.server_v2node.entity import ServerV2Node
from app.models.setting.entity import Setting


async def _seed_setting(db: AsyncSession, key: str, value: str, type_: str = "str") -> None:
    db.add(Setting(key=key, value=value, type=type_))


async def _seed_config_data(engine) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        await _seed_setting(db, "server_token", "secret")
        await _seed_setting(db, "server_push_interval", "30", "int")
        await _seed_setting(db, "server_pull_interval", "45", "int")
        await _seed_setting(db, "server_node_report_min_traffic", "100", "int")
        await _seed_setting(db, "server_device_online_min_traffic", "200", "int")

        route1 = ServerRoute(
            remarks="route 1",
            match='["domain:example.com"]',
            action="block",
            action_value=None,
        )
        route2 = ServerRoute(
            remarks="route 2",
            match="ip",
            action="direct",
            action_value="",
        )
        db.add_all([route1, route2])
        await db.flush()

        node = ServerV2Node(
            group_id="[1]",
            route_id=f"[{route2.id},{route1.id}]",
            name="v2node",
            host="node.example.com",
            listen_ip="127.0.0.1",
            port="443",
            server_port=443,
            tags='["tag"]',
            rate="1",
            show=True,
            sort=1,
            protocol="vless",
            tls=1,
            tls_settings='{"server_name":"example.com"}',
            flow="xtls-rprx-vision",
            network="tcp",
            network_settings='{"path":"/ws"}',
            encryption="none",
            encryption_settings='{"allow_insecure":false}',
            disable_sni=False,
            udp_relay_mode=None,
            zero_rtt_handshake=True,
            congestion_control="bbr",
            cipher="2022-blake3-aes-128-gcm",
            up_mbps=0,
            down_mbps=0,
            obfs="salamander",
            obfs_password="pwd",
            padding_scheme='["stop=8"]',
            created_at=1700000000,
            updated_at=1700000000,
        )
        db.add(node)
        await db.commit()
        return int(node.id)


@pytest.mark.asyncio
async def test_v2_server_config_token_validation(client, engine):
    res = await client.get("/api/v2/server/config?node_id=1")
    assert res.status_code == 200
    assert res.json() == {"status": "fail", "message": "token is null"}

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        await _seed_setting(db, "server_token", "secret")
        await db.commit()

    res = await client.get("/api/v2/server/config?token=bad&node_id=1")
    assert res.status_code == 200
    assert res.json() == {"status": "fail", "message": "token is error"}


@pytest.mark.asyncio
async def test_v2_server_config_missing_node(client, engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        await _seed_setting(db, "server_token", "secret")
        await db.commit()

    res = await client.get("/api/v2/server/config?token=secret&node_id=999")
    assert res.status_code == 200
    assert res.json() == {"status": "fail", "message": "server is not exist"}


@pytest.mark.asyncio
async def test_v2_server_config_success_and_etag(client, engine):
    node_id = await _seed_config_data(engine)

    res = await client.post("/api/v2/server/config", json={"token": "secret", "node_id": node_id})
    assert res.status_code == 200
    assert res.headers["etag"].startswith('"')

    data = res.json()
    assert data["listen_ip"] == "127.0.0.1"
    assert data["server_port"] == 443
    assert data["network"] == "tcp"
    assert data["network_settings"] == {"path": "/ws"}
    assert data["protocol"] == "vless"
    assert data["tls"] == 1
    assert data["tls_settings"] == {"server_name": "example.com"}
    assert data["encryption"] == "none"
    assert data["encryption_settings"] == {"allow_insecure": False}
    assert data["flow"] == "xtls-rprx-vision"
    assert data["cipher"] == "2022-blake3-aes-128-gcm"
    assert data["congestion_control"] == "bbr"
    assert data["zero_rtt_handshake"] is True
    assert data["up_mbps"] == 0
    assert data["down_mbps"] == 0
    assert data["obfs"] == "salamander"
    assert data["obfs_password"] == "pwd"
    assert data["padding_scheme"] == ["stop=8"]
    assert data["ignore_client_bandwidth"] is True
    assert data["base_config"] == {
        "push_interval": 30,
        "pull_interval": 45,
        "node_report_min_traffic": 100,
        "device_online_min_traffic": 200,
    }
    assert data["routes"] == [
        {"id": 2, "match": "ip", "action": "direct", "action_value": ""},
        {"id": 1, "match": ["domain:example.com"], "action": "block", "action_value": None},
    ]
    digest = hashlib.md5(b"1700000000").hexdigest()[:16]
    assert data["server_key"] == base64.b64encode(digest.encode()).decode()

    etag = res.headers["etag"].strip('"')
    res = await client.post(
        "/api/v2/server/config",
        json={"token": "secret", "node_id": node_id},
        headers={"If-None-Match": f'"{etag}"'},
    )
    assert res.status_code == 304
    assert res.headers["etag"] == f'"{etag}"'
