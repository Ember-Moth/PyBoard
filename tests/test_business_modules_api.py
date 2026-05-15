"""补齐业务模块 API 测试。"""

import json
import time

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.models.giftcard_redemption.entity import GiftcardRedemption
from app.models.log_event.entity import LogEvent
from app.payments.epay import EPay


async def _create_plan(client: AsyncClient, price: int = 1000, capacity_limit: int | None = None) -> int:
    payload = {
        "name": "Business",
        "group_id": 1,
        "transfer_enable": 10 * 1024**3,
        "show": True,
        "month_price": price,
    }
    if capacity_limit is not None:
        payload["capacity_limit"] = capacity_limit
    response = await client.post(
        "/api/v1/admin/plans",
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


@pytest.mark.asyncio
async def test_coupon_discount_applies_to_order_without_consuming_until_paid(admin_client: AsyncClient, session):
    now = int(time.time())
    plan_id = await _create_plan(admin_client, price=1000)
    response = await admin_client.post(
        "/api/v1/admin/coupons",
        json={
            "code": "SAVE200",
            "name": "Save 200",
            "type": 1,
            "value": 200,
            "show": True,
            "limit_use": 1,
            "started_at": now - 60,
            "ended_at": now + 3600,
        },
    )
    assert response.status_code == 201, response.text
    coupon_id = response.json()["data"]["id"]

    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": plan_id, "period": "month_price", "coupon_code": "SAVE200"},
    )
    assert response.status_code == 200, response.text
    trade_no = response.json()["data"]

    response = await admin_client.get(f"/api/v1/orders/detail?trade_no={trade_no}")
    assert response.status_code == 200
    order = response.json()["data"]["order"]
    assert order["total_amount"] == 800
    assert order["discount_amount"] == 200
    assert order["coupon_id"] is not None

    response = await admin_client.get(f"/api/v1/admin/coupons/{coupon_id}")
    assert response.status_code == 200
    assert response.json()["data"]["limit_use"] == 1

    response = await admin_client.post("/api/v1/orders/cancel", json={"trade_no": trade_no})
    assert response.status_code == 200
    response = await admin_client.get(f"/api/v1/admin/coupons/{coupon_id}")
    assert response.json()["data"]["limit_use"] == 1

    result = await session.execute(
        select(LogEvent.event).where(LogEvent.target_type == "order").where(LogEvent.target_id == trade_no)
    )
    events = set(result.scalars().all())
    assert {"order.created", "order.cancelled"}.issubset(events)


@pytest.mark.asyncio
async def test_coupon_consumes_on_zero_amount_checkout(admin_client: AsyncClient):
    now = int(time.time())
    plan_id = await _create_plan(admin_client, price=1000)
    response = await admin_client.post(
        "/api/v1/admin/coupons",
        json={
            "code": "FREEPLAN",
            "name": "Free Plan",
            "type": 1,
            "value": 1000,
            "show": True,
            "limit_use": 1,
            "started_at": now - 60,
            "ended_at": now + 3600,
        },
    )
    assert response.status_code == 201, response.text
    coupon_id = response.json()["data"]["id"]

    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": plan_id, "period": "month_price", "coupon_code": "FREEPLAN"},
    )
    assert response.status_code == 200, response.text
    trade_no = response.json()["data"]
    response = await admin_client.get(f"/api/v1/admin/coupons/{coupon_id}")
    assert response.json()["data"]["limit_use"] == 1

    response = await admin_client.post("/api/v1/orders/checkout", json={"trade_no": trade_no, "method": 0})
    assert response.status_code == 200, response.text
    response = await admin_client.get(f"/api/v1/admin/coupons/{coupon_id}")
    assert response.json()["data"]["limit_use"] == 0


@pytest.mark.asyncio
async def test_giftcard_redeem_adds_balance_once(admin_client: AsyncClient, session):
    now = int(time.time())
    response = await admin_client.post(
        "/api/v1/admin/giftcards",
        json={
            "code": "BALANCE500",
            "name": "Balance",
            "type": 1,
            "value": 500,
            "started_at": now - 60,
            "ended_at": now + 3600,
        },
    )
    assert response.status_code == 201, response.text
    giftcard_id = response.json()["data"]["id"]

    response = await admin_client.post("/api/v1/giftcards/redeem", json={"code": "BALANCE500"})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["type"] == 1

    response = await admin_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["balance"] == 500

    response = await admin_client.post("/api/v1/giftcards/redeem", json={"code": "BALANCE500"})
    assert response.status_code == 400

    result = await session.execute(
        select(GiftcardRedemption).where(GiftcardRedemption.giftcard_id == giftcard_id)
    )
    records = list(result.scalars().all())
    assert len(records) == 1
    assert records[0].code == "BALANCE500"


@pytest.mark.asyncio
async def test_plan_capacity_is_rechecked_when_paid(admin_client: AsyncClient):
    admin_token = admin_client.headers["Authorization"]
    plan_id = await _create_plan(admin_client, price=1000, capacity_limit=1)

    response = await admin_client.post(
        "/api/v1/auth/register",
        json={"email": "capacity-1@test.local", "password": "password123"},
    )
    assert response.status_code == 201, response.text
    user1_token = response.json()["data"]["auth_token"]
    response = await admin_client.post(
        "/api/v1/auth/register",
        json={"email": "capacity-2@test.local", "password": "password123"},
    )
    assert response.status_code == 201, response.text
    user2_token = response.json()["data"]["auth_token"]

    admin_client.headers["Authorization"] = user1_token
    response = await admin_client.post("/api/v1/orders", json={"plan_id": plan_id, "period": "month_price"})
    assert response.status_code == 200, response.text
    trade_no1 = response.json()["data"]

    admin_client.headers["Authorization"] = user2_token
    response = await admin_client.post("/api/v1/orders", json={"plan_id": plan_id, "period": "month_price"})
    assert response.status_code == 200, response.text
    trade_no2 = response.json()["data"]

    admin_client.headers["Authorization"] = admin_token
    response = await admin_client.post("/api/v1/admin/orders/paid", json={"trade_no": trade_no1})
    assert response.status_code == 200, response.text

    response = await admin_client.post("/api/v1/admin/orders/paid", json={"trade_no": trade_no2})
    assert response.status_code == 400
    assert "售罄" in response.json()["msg"]

    admin_client.headers["Authorization"] = user2_token
    response = await admin_client.get(f"/api/v1/orders/check?trade_no={trade_no2}")
    assert response.status_code == 200
    assert response.json()["data"] == 0


@pytest.mark.asyncio
async def test_ticket_user_create_and_admin_reply(admin_client: AsyncClient):
    admin_token = admin_client.headers["Authorization"]
    response = await admin_client.post(
        "/api/v1/auth/register",
        json={"email": "ticket-user@test.local", "password": "password123"},
    )
    assert response.status_code == 201, response.text
    admin_client.headers["Authorization"] = response.json()["data"]["auth_token"]
    response = await admin_client.post(
        "/api/v1/tickets",
        json={"subject": "Need help", "level": 1, "message": "hello"},
    )
    assert response.status_code == 201, response.text
    ticket_id = response.json()["data"]["ticket"]["id"]

    admin_client.headers["Authorization"] = admin_token
    response = await admin_client.post(
        f"/api/v1/admin/tickets/{ticket_id}/reply",
        json={"message": "processed"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["ticket"]["reply_status"] == 1
    assert data["messages"][-1]["message"] == "processed"


@pytest.mark.asyncio
async def test_invite_registration_and_commission(admin_client: AsyncClient, session):
    admin_token = admin_client.headers["Authorization"]
    admin_id = (await admin_client.get("/api/v1/auth/me")).json()["data"]["id"]
    response = await admin_client.post("/api/v1/admin/invite/codes", json={"user_id": admin_id})
    assert response.status_code == 201, response.text
    invite_code = response.json()["data"]["code"]

    response = await admin_client.post(
        "/api/v1/auth/register",
        json={"email": "invitee@test.local", "password": "password123", "invite_code": invite_code},
    )
    assert response.status_code == 201, response.text
    invitee_token = response.json()["data"]["auth_token"]

    admin_client.headers["Authorization"] = admin_token
    plan_id = await _create_plan(admin_client, price=1000)
    config = {"url": "https://pay.example.com", "pid": "123", "key": "test", "type": ""}
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "EPay",
            "name": "EPay",
            "config": json.dumps(config),
            "enable": True,
        },
    )
    assert response.status_code == 201, response.text
    payment = response.json()["data"]

    admin_client.headers["Authorization"] = invitee_token
    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": plan_id, "period": "month_price"},
    )
    assert response.status_code == 200, response.text
    trade_no = response.json()["data"]
    response = await admin_client.post(
        "/api/v1/orders/checkout",
        json={"trade_no": trade_no, "method": payment["id"]},
    )
    assert response.status_code == 200, response.text

    params = {
        "pid": "123",
        "trade_no": "gw-1",
        "out_trade_no": trade_no,
        "type": "alipay",
        "name": trade_no,
        "money": "10",
        "trade_status": "TRADE_SUCCESS",
    }
    params["sign"] = EPay(config)._generate_sign(params)
    params["sign_type"] = "MD5"
    response = await admin_client.post(f"/notify/epay/{payment['uuid']}", json=params)
    assert response.status_code == 200
    assert response.text == '"success"'

    admin_client.headers["Authorization"] = admin_token
    response = await admin_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["commission_balance"] == 100

    result = await session.execute(
        select(LogEvent)
        .where(LogEvent.category == "commission")
        .where(LogEvent.event == "commission.granted")
        .where(LogEvent.target_id == trade_no)
    )
    event = result.scalar_one()
    assert event.data["get_amount"] == 100
    assert event.data["order_amount"] == 1000


@pytest.mark.asyncio
async def test_mail_send_failure_writes_log(admin_client: AsyncClient, session):
    response = await admin_client.post(
        "/api/v1/admin/mail/send",
        json={
            "email": "user@test.local",
            "subject": "Hello",
            "template_name": "system_notify",
            "template_value": {"content": "hello"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"] is False

    response = await admin_client.get("/api/v1/admin/mail/logs")
    assert response.status_code == 200
    logs = response.json()["data"]
    assert len(logs) == 1
    assert logs[0]["error"] == "邮件 SMTP 配置不完整"

    result = await session.execute(select(LogEvent).where(LogEvent.category == "mail"))
    event = result.scalar_one()
    assert event.event == "mail.failed"
    assert event.level == "error"
    assert event.data["email"] == "user@test.local"
