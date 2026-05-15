"""订阅模块测试。"""

import base64
import json
import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.plan.entity import Plan
from app.models.knowledge.entity import Knowledge
from app.models.server_v2node.entity import ServerV2Node
from app.models.setting.entity import Setting
from app.models.user.entity import User


@pytest.mark.asyncio
async def test_user_subscribe_info_servers_and_client_subscription(authed_client, engine):
    await _prepare_subscription_data(engine)

    res = await authed_client.get("/api/v1/user/subscribe")
    assert res.status_code == 200
    payload = res.json()["data"]
    assert payload["plan"]["name"] == "Subscribe Plan"
    assert payload["subscribe_url"].startswith("https://panel.example.com/api/v1/client/subscribe?token=")
    token = payload["token"]

    res = await authed_client.get("/api/v1/user/servers")
    assert res.status_code == 200
    servers = res.json()["data"]
    assert len(servers) == 1
    assert servers[0]["protocol"] == "vmess"
    etag = res.headers["etag"]

    res = await authed_client.get("/api/v1/user/servers", headers={"If-None-Match": etag})
    assert res.status_code == 304

    res = await authed_client.get(f"/api/v1/client/subscribe?token={token}")
    assert res.status_code == 200
    decoded = base64.b64decode(res.text).decode()
    assert "vmess://" in decoded

    res = await authed_client.get(f"/api/v1/client/subscribe?token={token}&flag=clash-meta")
    assert res.status_code == 200
    assert "proxies:" in res.text
    assert "Subscribe Node" in res.text


@pytest.mark.asyncio
async def test_subscribe_supports_all_PyBoard_client_formats(authed_client, engine):
    await _prepare_subscription_data(engine, with_all_protocols=True)
    token = (await authed_client.get("/api/v1/user/subscribe")).json()["data"]["token"]

    base64_flags = [
        "general",
        "passwall",
        "ssrplus",
        "v2rayn",
        "v2rayng",
        "v2raytun",
        "sagernet",
        "shadowrocket",
        "quantumult%20x",
    ]
    for flag in base64_flags:
        res = await authed_client.get(f"/api/v1/client/subscribe?token={token}&flag={flag}")
        assert res.status_code == 200, flag
        decoded = base64.b64decode(res.text).decode()
        assert "vmess://" in decoded or "STATUS=" in decoded or "tag=Subscribe Node" in decoded, flag

    yaml_flags = ["clash", "clash-meta", "clash-verge", "nyanpasu", "stash"]
    for flag in yaml_flags:
        res = await authed_client.get(f"/api/v1/client/subscribe?token={token}&flag={flag}")
        assert res.status_code == 200, flag
        assert "proxies:" in res.text
        assert "VLESS Node" in res.text
        assert "TUIC Node" in res.text

    res = await authed_client.get(f"/api/v1/client/subscribe?token={token}&flag=sing-box 1.12.0")
    assert res.status_code == 200
    singbox = res.json()
    outbound_types = {item["type"] for item in singbox["outbounds"]}
    assert {"selector", "vmess", "vless", "trojan", "shadowsocks", "hysteria2", "tuic", "anytls"} <= outbound_types

    res = await authed_client.get(f"/api/v1/client/subscribe?token={token}&flag=sing-box 1.11.0")
    assert res.status_code == 200
    assert res.json()["outbounds"][0]["type"] == "selector"

    for flag, marker in [
        ("surge", "[Proxy]"),
        ("surfboard", "[Proxy Group]"),
        ("loon", "Subscribe Node=vmess"),
        ("shadowsocks", '"servers"'),
    ]:
        res = await authed_client.get(f"/api/v1/client/subscribe?token={token}&flag={flag}")
        assert res.status_code == 200, flag
        assert marker in res.text


@pytest.mark.asyncio
async def test_subscribe_rejects_expired_or_wrong_token(authed_client, engine):
    await _prepare_subscription_data(engine, expired=True)
    token = (await authed_client.get("/api/v1/user/subscribe")).json()["data"]["token"]

    res = await authed_client.get(f"/api/v1/client/subscribe?token={token}")
    assert res.status_code == 403

    res = await authed_client.get("/api/v1/client/subscribe?token=bad")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_subscribe_one_time_token(client, authed_client, engine):
    await _prepare_subscription_data(engine)
    await _set_setting(engine, "show_subscribe_method", "1", "int")

    res = await authed_client.get("/api/v1/user/subscribe")
    url = res.json()["data"]["subscribe_url"]
    one_time_token = url.rsplit("token=", 1)[-1]

    res = await client.get(f"/api/v1/client/subscribe?token={one_time_token}")
    assert res.status_code == 200
    assert "vmess://" in base64.b64decode(res.text).decode()

    res = await client.get(f"/api/v1/client/subscribe?token={one_time_token}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_knowledge_renders_subscribe_variables_and_access_block(client, engine):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "knowledge-sub@test.local", "password": "password123"},
    )
    token = register.json()["data"]["auth_token"]
    await _prepare_subscription_data(engine, email="knowledge-sub@test.local")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(
            Knowledge(
                language="zh-CN",
                category="client",
                title="Template",
                body="站点 {{ siteName }} {{ subscribeToken }} <!--access start-->{{ subscribeUrl }}<!--access end-->",
                show=True,
            )
        )
        await db.commit()

    res = await client.get("/api/v1/knowledge/1")
    assert res.status_code == 200
    assert "https://panel.example.com" not in res.json()["data"]["body"]

    res = await client.get("/api/v1/knowledge/1", headers={"Authorization": token})
    assert res.status_code == 200
    body = res.json()["data"]["body"]
    assert "PyBoard" in body
    assert "https://panel.example.com/api/v1/client/subscribe?token=" in body


async def _prepare_subscription_data(
    engine,
    *,
    expired: bool = False,
    email: str = "user@test.local",
    with_all_protocols: bool = False,
) -> None:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add_all(
            [
                Setting(key="app_url", value="https://panel.example.com", type="str"),
                Setting(key="subscribe_path", value="/api/v1/client/subscribe", type="str"),
            ]
        )
        plan = Plan(
            group_id=1,
            transfer_enable=1024 * 1024 * 1024,
            name="Subscribe Plan",
            show=True,
        )
        db.add(plan)
        await db.flush()

        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        user.plan_id = plan.id
        user.group_id = 1
        user.transfer_enable = plan.transfer_enable
        user.expired_at = int(time.time()) - 60 if expired else int(time.time()) + 86400
        user.uuid = "11111111-1111-4111-8111-111111111111"

        db.add_all(_subscription_nodes(with_all_protocols))
        await db.commit()


def _subscription_nodes(with_all_protocols: bool) -> list[ServerV2Node]:
    nodes = [
        _node(
            "Subscribe Node",
            "vmess",
            port="443",
            tls=1,
            tls_settings={"server_name": "node.example.com", "allow_insecure": 0},
            network="ws",
            network_settings={"path": "/ws", "headers": {"Host": "node.example.com"}},
        )
    ]
    if not with_all_protocols:
        return nodes
    nodes.extend(
        [
            _node(
                "SS Node",
                "shadowsocks",
                host="ss.example.com",
                port="8388",
                server_port=8388,
                cipher="aes-128-gcm",
            ),
            _node(
                "VLESS Node",
                "vless",
                host="vless.example.com",
                port="8443",
                server_port=8443,
                tls=2,
                tls_settings={
                    "server_name": "vless.example.com",
                    "public_key": "public-key",
                    "short_id": "abcd",
                    "fingerprint": "chrome",
                },
                flow="xtls-rprx-vision",
            ),
            _node(
                "Trojan Node",
                "trojan",
                host="trojan.example.com",
                port="9443",
                server_port=9443,
                tls=1,
                tls_settings={"server_name": "trojan.example.com"},
            ),
            _node(
                "Hysteria2 Node",
                "hysteria2",
                host="hy2.example.com",
                port="2083",
                server_port=2083,
                tls=1,
                tls_settings={"server_name": "hy2.example.com"},
                obfs="salamander",
                obfs_password="obfs-password",
                up_mbps=100,
                down_mbps=100,
            ),
            _node(
                "TUIC Node",
                "tuic",
                host="tuic.example.com",
                port="4433",
                server_port=4433,
                tls=1,
                tls_settings={"server_name": "tuic.example.com"},
                congestion_control="bbr",
                udp_relay_mode="native",
            ),
            _node(
                "AnyTLS Node",
                "anytls",
                host="anytls.example.com",
                port="4434",
                server_port=4434,
                tls=1,
                tls_settings={"server_name": "anytls.example.com"},
            ),
        ]
    )
    return nodes


def _node(
    name: str,
    protocol: str,
    *,
    host: str = "node.example.com",
    port: str = "443",
    server_port: int = 443,
    tls: int = 0,
    tls_settings: dict | None = None,
    network: str = "tcp",
    network_settings: dict | None = None,
    cipher: str | None = None,
    flow: str | None = None,
    obfs: str | None = None,
    obfs_password: str | None = None,
    up_mbps: int = 0,
    down_mbps: int = 0,
    congestion_control: str | None = None,
    udp_relay_mode: str | None = None,
) -> ServerV2Node:
    return ServerV2Node(
        group_id=json.dumps([1]),
        name=name,
        host=host,
        listen_ip="0.0.0.0",
        port=port,
        server_port=server_port,
        rate="1",
        show=True,
        protocol=protocol,
        tls=tls,
        tls_settings=json.dumps(tls_settings or {}),
        network=network,
        network_settings=json.dumps(network_settings or {}),
        cipher=cipher,
        flow=flow,
        obfs=obfs,
        obfs_password=obfs_password,
        up_mbps=up_mbps,
        down_mbps=down_mbps,
        congestion_control=congestion_control,
        udp_relay_mode=udp_relay_mode,
        sort=1,
    )


async def _set_setting(engine, key: str, value: str, type_: str = "str") -> None:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(Setting(key=key, value=value, type=type_))
        await db.commit()
