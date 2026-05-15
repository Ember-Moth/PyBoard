"""UniProxy 服务端接口测试。"""

import time

import msgpack
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.queue import get_queue
from app.models.server_v2node.entity import ServerV2Node
from app.models.setting.entity import Setting
from app.models.user.entity import User
from main import app


class FakeQueue:
    def __init__(self):
        self.jobs = []

    async def enqueue_job(self, name, *args, **kwargs):
        self.jobs.append((name, args, kwargs))


async def _seed_uniproxy_data(engine) -> tuple[int, int]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(Setting(key="server_token", value="secret", type="str"))
        node = ServerV2Node(
            group_id="[1]",
            route_id=None,
            name="vless-node",
            host="node.example.com",
            listen_ip="0.0.0.0",
            port="443",
            server_port=443,
            rate="2",
            protocol="vless",
            tls=1,
            network="tcp",
            show=True,
            up_mbps=0,
            down_mbps=0,
        )
        user = User(
            email="node-user@test.local",
            password="hash",
            token="node-token",
            uuid="node-uuid",
            group_id=1,
            u=10,
            d=10,
            transfer_enable=1000,
            expired_at=int(time.time()) + 3600,
            device_limit=2,
            speed_limit=100,
        )
        db.add_all([node, user])
        await db.commit()
        return int(node.id), int(user.id)


@pytest.mark.asyncio
async def test_uniproxy_user_json_msgpack_and_etag(client, engine):
    node_id, user_id = await _seed_uniproxy_data(engine)
    url = f"/api/v1/server/UniProxy/user?token=secret&node_type=vless&node_id={node_id}"

    res = await client.get(url)
    assert res.status_code == 200
    user = res.json()["users"][0]
    assert user == {
        "id": user_id,
        "uuid": "node-uuid",
        "speed_limit": 100,
        "device_limit": 2,
        "u": 10,
        "d": 10,
        "transfer_enable": 1000,
        "expired_at": user["expired_at"],
        "t": 0,
        "group_id": 1,
    }
    assert user["expired_at"] > int(time.time())
    assert "password" not in user
    assert "token" not in user
    assert "email" not in user
    etag = res.headers["etag"].strip('"')

    res = await client.get(url, headers={"If-None-Match": f'"{etag}"'})
    assert res.status_code == 304

    res = await client.get(url, headers={"X-Response-Format": "msgpack"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/x-msgpack"
    assert msgpack.unpackb(res.content, raw=False)["users"][0]["id"] == user_id


@pytest.mark.asyncio
async def test_uniproxy_push_enqueues_traffic_jobs(client, engine, cache):
    node_id, _user_id = await _seed_uniproxy_data(engine)
    queue = FakeQueue()
    app.dependency_overrides[get_queue] = lambda: queue
    try:
        res = await client.post(
            f"/api/v1/server/UniProxy/push?token=secret&node_type=vless&node_id={node_id}",
            json={"1": [100, 200]},
        )
    finally:
        app.dependency_overrides.pop(get_queue, None)

    assert res.status_code == 200
    assert res.json() == {"data": True}
    assert [job[0] for job in queue.jobs] == ["traffic_fetch", "stat_user", "stat_server"]
    assert await cache.get(f"SERVER_VLESS_ONLINE_USER_{node_id}") == 1
    assert await cache.get(f"SERVER_VLESS_LAST_PUSH_AT_{node_id}") is not None


@pytest.mark.asyncio
async def test_uniproxy_alive_and_alivelist(client, engine):
    node_id, user_id = await _seed_uniproxy_data(engine)
    base = "/api/v1/server/UniProxy"
    params = f"token=secret&node_type=vless&node_id={node_id}"

    res = await client.post(f"{base}/alive?{params}", json={str(user_id): ["1.1.1.1_a", "2.2.2.2_b"]})
    assert res.status_code == 200
    assert res.json() == {"data": True}

    res = await client.get(f"{base}/alivelist?{params}")
    assert res.status_code == 200
    assert res.json() == {"alive": {str(user_id): 2}}


@pytest.mark.asyncio
async def test_uniproxy_does_not_expose_config(client, engine):
    node_id, _user_id = await _seed_uniproxy_data(engine)
    res = await client.get(f"/api/v1/server/UniProxy/config?token=secret&node_type=vless&node_id={node_id}")
    assert res.status_code == 404
