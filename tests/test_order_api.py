"""订单 API 测试。"""

import json
import urllib.parse

import pytest
from httpx import AsyncClient

from app.payments import PaymentRequest
from app.payments.epay import EPay


@pytest.mark.asyncio
async def test_get_payment_methods(client: AsyncClient):
    """获取支付方式列表。"""
    response = await client.get("/api/v1/payment-methods")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_create_order_no_auth(client: AsyncClient):
    """未登录创建订单。"""
    response = await client.post(
        "/api/v1/orders",
        json={"plan_id": 1, "period": "month_price", "deposit_amount": 1000},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_order_rejects_non_price_period(admin_client: AsyncClient):
    """创建订单时只能使用套餐价格字段。"""
    response = await admin_client.post(
        "/api/v1/admin/plans",
        json={
            "name": "Basic",
            "group_id": 1,
            "transfer_enable": 10 * 1024**3,
            "show": True,
            "month_price": 1000,
        },
    )
    plan_id = response.json()["data"]["id"]

    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": plan_id, "period": "id"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_deposit_order_flow(authed_client: AsyncClient):
    """充值订单完整流程。"""
    # 1. 创建充值订单
    response = await authed_client.post(
        "/api/v1/orders",
        json={"plan_id": 0, "period": "deposit", "deposit_amount": 1000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], str)
    trade_no = data["data"]

    # 2. 获取订单列表
    response = await authed_client.get("/api/v1/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    # 3. 获取订单详情
    response = await authed_client.get(f"/api/v1/orders/detail?trade_no={trade_no}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "order" in data["data"]

    # 4. 检查订单状态
    response = await authed_client.get(f"/api/v1/orders/check?trade_no={trade_no}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"] == 0  # 待支付

    # 5. 取消订单
    response = await authed_client.post(
        "/api/v1/orders/cancel",
        json={"trade_no": trade_no},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"] is True


@pytest.mark.asyncio
async def test_admin_orders(admin_client: AsyncClient):
    """管理端订单列表。"""
    response = await admin_client.get("/api/v1/admin/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_admin_payments(admin_client: AsyncClient):
    """管理端支付方式管理。"""
    # 1. 创建支付方式
    config = json.dumps(
        {"url": "https://pay.example.com", "pid": "123", "key": "test", "type": ""}
    )
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "EPay",
            "name": "易支付",
            "config": config,
            "enable": True,
            "sort": 1,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == 201
    payment_id = data["data"]["id"]

    # 2. 获取列表
    response = await admin_client.get("/api/v1/admin/payment-methods")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]) > 0

    # 3. 获取详情
    response = await admin_client.get(f"/api/v1/admin/payment-methods/{payment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["name"] == "易支付"

    # 4. 更新
    response = await admin_client.patch(
        f"/api/v1/admin/payment-methods/{payment_id}",
        json={"name": "易支付(更新)"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["name"] == "易支付(更新)"

    # 5. 删除
    response = await admin_client.delete(f"/api/v1/admin/payment-methods/{payment_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_payment_gateways(admin_client: AsyncClient):
    """管理端可获取已注册支付网关和配置表单。"""
    response = await admin_client.get("/api/v1/admin/payment-methods/gateways")
    assert response.status_code == 200
    gateways = response.json()["data"]
    epay = next(item for item in gateways if item["payment"] == "EPay")
    assert epay["route"] == "epay"
    assert set(epay["form"]) == {"url", "pid", "key", "type"}


@pytest.mark.asyncio
async def test_delete_payment_rejects_referenced_method(admin_client: AsyncClient):
    """已有订单引用的支付方式不能删除。"""
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "EPay",
            "name": "易支付",
            "config": json.dumps({"url": "https://pay.example.com", "pid": "123", "key": "test"}),
            "enable": True,
        },
    )
    assert response.status_code == 201, response.text
    payment = response.json()["data"]

    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": 0, "period": "deposit", "deposit_amount": 1000},
    )
    assert response.status_code == 200, response.text
    trade_no = response.json()["data"]

    response = await admin_client.post(
        "/api/v1/orders/checkout",
        json={"trade_no": trade_no, "method": payment["id"]},
    )
    assert response.status_code == 200, response.text

    response = await admin_client.delete(f"/api/v1/admin/payment-methods/{payment['id']}")
    assert response.status_code == 409
    assert "订单引用" in response.json()["msg"]


@pytest.mark.asyncio
async def test_create_payment_accepts_gateway_alias(admin_client: AsyncClient):
    """支付网关标识支持别名，入库统一为规范名称。"""
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "epay",
            "name": "易支付",
            "config": json.dumps(
                {"url": "https://pay.example.com", "pid": "123", "key": "test"}
            ),
            "enable": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["payment"] == "EPay"


@pytest.mark.asyncio
async def test_create_payment_rejects_unknown_gateway(admin_client: AsyncClient):
    """未注册的支付网关不能创建。"""
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "UnknownPay",
            "name": "未知支付",
            "config": "{}",
            "enable": True,
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_epay_notify_rejects_wrong_amount(admin_client: AsyncClient):
    """支付回调金额必须和订单应付金额一致。"""
    config = {"url": "https://pay.example.com", "pid": "123", "key": "test", "type": ""}
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "EPay",
            "name": "易支付",
            "config": json.dumps(config),
            "enable": True,
        },
    )
    payment = response.json()["data"]

    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": 0, "period": "deposit", "deposit_amount": 1000},
    )
    trade_no = response.json()["data"]

    response = await admin_client.post(
        "/api/v1/orders/checkout",
        json={"trade_no": trade_no, "method": payment["id"]},
    )
    assert response.status_code == 200

    params = {
        "money": "0.01",
        "out_trade_no": trade_no,
        "pid": config["pid"],
        "trade_no": "gateway-1",
        "trade_status": "TRADE_SUCCESS",
    }
    params["sign"] = EPay(config)._generate_sign(params)
    params["sign_type"] = "MD5"

    response = await admin_client.post(f"/notify/epay/{payment['uuid']}", json=params)
    assert response.status_code == 200
    assert response.json() == "fail"

    response = await admin_client.get(f"/api/v1/orders/check?trade_no={trade_no}")
    assert response.json()["data"] == 0


@pytest.mark.asyncio
async def test_checkout_returns_epay_submit_url(admin_client: AsyncClient):
    """后端只生成 EPay submit.php URL，由前端负责跳转。"""
    config = {"url": "https://pay.example.com", "pid": "123", "key": "test", "type": ""}
    response = await admin_client.post(
        "/api/v1/admin/payment-methods",
        json={
            "payment": "EPay",
            "name": "易支付",
            "config": json.dumps(config),
            "enable": True,
        },
    )
    payment = response.json()["data"]

    response = await admin_client.post(
        "/api/v1/orders",
        json={"plan_id": 0, "period": "deposit", "deposit_amount": 1000},
    )
    trade_no = response.json()["data"]

    response = await admin_client.post(
        "/api/v1/orders/checkout",
        json={"trade_no": trade_no, "method": payment["id"]},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["type"] == 1
    assert payload["data"].startswith("https://pay.example.com/submit.php?")


def test_epay_pay_builds_php_compatible_url():
    """EPay 发起支付参数格式应兼容 PHP 版实现。"""
    config = {"url": "https://pay.example.com", "pid": "123", "key": "test", "type": ""}
    result = EPay(config).pay(
        PaymentRequest(
            trade_no="T123",
            total_amount=1000,
            notify_url="https://panel.example.com/notify/epay/u1",
            return_url="https://panel.example.com/#/order/T123",
        )
    )

    parsed = urllib.parse.urlparse(result["data"])
    params = dict(urllib.parse.parse_qsl(parsed.query))
    sign = params.pop("sign")
    params.pop("sign_type")

    assert result["type"] == 1
    assert parsed.geturl().startswith("https://pay.example.com/submit.php?")
    assert params["money"] == "10"
    assert params["notify_url"] == "https://panel.example.com/notify/epay/u1"
    assert sign == EPay(config)._generate_sign(params)


def test_epay_sign_ignores_empty_and_signature_fields():
    """EPay 签名应排除 sign/sign_type 和空值。"""
    config = {"url": "https://pay.example.com", "pid": "123", "key": "test"}
    epay = EPay(config)
    base = {
        "money": "10",
        "name": "T123",
        "notify_url": "https://panel.example.com/notify/epay/u1",
        "out_trade_no": "T123",
        "pid": "123",
        "return_url": "https://panel.example.com/#/order/T123",
    }
    with_ignored = {
        **base,
        "empty": "",
        "none": None,
        "sign": "bad",
        "sign_type": "MD5",
    }

    assert epay._generate_sign(with_ignored) == epay._generate_sign(base)
