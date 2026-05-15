"""Admin HTML UI 测试。"""

import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.failed_job.entity import FailedJob
from app.models.plan.entity import Plan
from app.repositories.coupon import CouponRepository
from app.repositories.giftcard import GiftcardRepository
from app.repositories.knowledge import KnowledgeRepository
from app.repositories.notice import NoticeRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.plan import PlanRepository
from app.repositories.server_group import ServerGroupRepository
from app.repositories.server_route import ServerRouteRepository
from app.repositories.server_v2node import ServerV2NodeRepository
from app.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_admin_ui_login_dashboard_and_users_flow(client, engine):
    await client.post("/api/v1/auth/register", json={"email": "admin-ui@test.local", "password": "password123"})
    await client.post("/api/v1/auth/register", json={"email": "normal-ui@test.local", "password": "password123"})
    await _promote_admin(engine, "admin-ui@test.local")

    res = await client.get("/admin/dashboard", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"].startswith("/admin/login")

    res = await client.get("/admin/login")
    assert res.status_code == 200
    csrf = client.cookies.get("admin_csrf")
    assert csrf

    res = await client.post(
        "/admin/login",
        content=f"csrf_token={csrf}&email=admin-ui%40test.local&password=password123&next=/admin/dashboard",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert res.status_code == 303
    assert client.cookies.get("admin_token")
    csrf = client.cookies.get("admin_csrf")
    assert csrf

    res = await client.get("/admin/dashboard")
    assert res.status_code == 200
    assert "/admin/fragments/dashboard/overview" in res.text
    assert 'id="navbar-menu"' in res.text
    assert "navbar-vertical" not in res.text
    assert "客户与支持" in res.text

    res = await client.get("/admin/fragments/dashboard/overview")
    assert res.status_code == 200
    assert "系统状态" in res.text

    res = await client.get("/admin/users")
    assert res.status_code == 200
    assert "/admin/fragments/users/table" in res.text

    res = await client.get("/admin/fragments/users/table")
    assert res.status_code == 200
    assert "normal-ui@test.local" in res.text

    res = await client.get("/admin/fragments/users/table?q=normal-ui")
    assert res.status_code == 200
    assert "normal-ui@test.local" in res.text
    assert "admin-ui@test.local" not in res.text

    res = await client.get("/admin/fragments/users/create-form?q=normal-ui")
    assert res.status_code == 200
    assert "创建用户" in res.text

    res = await client.post(
        "/admin/actions/users",
        data={
            "csrf_token": csrf,
            "email": "created-ui@test.local",
            "password": "password123",
            "q": "",
            "status": "",
            "offset": "0",
            "limit": "20",
        },
    )
    assert res.status_code == 200
    assert "created-ui@test.local" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#users-table"

    res = await client.get("/admin/fragments/users/generate-form")
    assert res.status_code == 200
    assert "批量生成用户" in res.text

    res = await client.post(
        "/admin/actions/users/generate",
        data={
            "csrf_token": csrf,
            "email_prefix": "bulk-ui",
            "email_suffix": "test.local",
            "password": "password123",
            "generate_count": "2",
            "q": "bulk-ui",
            "status": "",
            "offset": "0",
            "limit": "20",
        },
    )
    assert res.status_code == 200
    assert "bulk-ui1@test.local" in res.text
    assert "bulk-ui2@test.local" in res.text

    res = await client.post(
        "/admin/actions/users",
        data={"csrf_token": "wrong", "email": "bad-ui@test.local", "password": "password123"},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    user_id = await _user_id(engine, "normal-ui@test.local")
    res = await client.get(f"/admin/fragments/users/form?user_id={user_id}")
    assert res.status_code == 200
    assert "编辑用户" in res.text

    csrf = client.cookies.get("admin_csrf")
    res = await client.post(
        f"/admin/actions/users/{user_id}",
        content=f"csrf_token={csrf}&email=normal-ui%40test.local&balance=123&transfer_enable=0&expired_at=0",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    assert "normal-ui@test.local" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"

    created_id = await _user_id(engine, "created-ui@test.local")
    res = await client.post(
        f"/admin/actions/users/{created_id}/delete",
        data={
            "csrf_token": csrf,
            "q": "created-ui",
            "status": "",
            "offset": "0",
            "limit": "20",
        },
    )
    assert res.status_code == 200
    assert "created-ui@test.local" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_plan_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "plan-admin-ui@test.local")

    res = await client.get("/admin/plans")
    assert res.status_code == 200
    assert "/admin/fragments/plans/table" in res.text

    res = await client.get("/admin/fragments/plans/table")
    assert res.status_code == 200
    assert "暂无套餐" in res.text

    res = await client.get("/admin/fragments/plans/form")
    assert res.status_code == 200
    assert "创建套餐" in res.text

    res = await client.post(
        "/admin/actions/plans",
        data={
            "csrf_token": csrf,
            "name": "UI Basic",
            "group_id": "1",
            "transfer_enable": str(10 * 1024 * 1024),
            "month_price": "990",
            "show": "1",
            "renew": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Basic" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#plans-table"

    plan_id = await _plan_id(engine, "UI Basic")
    res = await client.get(f"/admin/fragments/plans/form?plan_id={plan_id}")
    assert res.status_code == 200
    assert "编辑套餐" in res.text

    res = await client.post(
        f"/admin/actions/plans/{plan_id}",
        data={
            "csrf_token": csrf,
            "name": "UI Pro",
            "group_id": "1",
            "transfer_enable": str(20 * 1024 * 1024),
            "month_price": "1990",
            "show": "1",
            "renew": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Pro" in res.text

    res = await client.post(
        "/admin/actions/plans",
        data={"csrf_token": "wrong", "name": "Bad", "group_id": "1", "transfer_enable": "1"},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    res = await client.post(
        f"/admin/actions/plans/{plan_id}/delete",
        data={"csrf_token": csrf},
    )
    assert res.status_code == 200
    assert "UI Pro" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_payment_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "payment-admin-ui@test.local")

    res = await client.get("/admin/payments")
    assert res.status_code == 200
    assert "/admin/fragments/payments/table" in res.text

    res = await client.get("/admin/fragments/payments/table")
    assert res.status_code == 200
    assert "暂无支付方式" in res.text

    res = await client.get("/admin/fragments/payments/form")
    assert res.status_code == 200
    assert "创建支付方式" in res.text
    assert "EPay" in res.text

    config = '{"url":"https://pay.test","pid":"1000","key":"secret","type":"alipay"}'
    res = await client.post(
        "/admin/actions/payments",
        data={
            "csrf_token": csrf,
            "payment": "EPay",
            "name": "UI EPay",
            "config": config,
            "handling_fee_fixed": "10",
            "handling_fee_percent": "1.5",
            "enable": "1",
        },
    )
    assert res.status_code == 200
    assert "UI EPay" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#payments-table"

    payment_id = await _payment_id(engine, "UI EPay")
    res = await client.get(f"/admin/fragments/payments/form?payment_id={payment_id}")
    assert res.status_code == 200
    assert "编辑支付方式" in res.text

    res = await client.post(
        f"/admin/actions/payments/{payment_id}",
        data={
            "csrf_token": csrf,
            "payment": "EPay",
            "name": "UI EPay Updated",
            "config": config,
            "handling_fee_fixed": "0",
            "handling_fee_percent": "0",
            "enable": "1",
        },
    )
    assert res.status_code == 200
    assert "UI EPay Updated" in res.text

    res = await client.post(
        "/admin/actions/payments",
        data={"csrf_token": "wrong", "payment": "EPay", "name": "Bad", "config": config},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    res = await client.post(
        f"/admin/actions/payments/{payment_id}/delete",
        data={"csrf_token": csrf},
    )
    assert res.status_code == 200
    assert "UI EPay Updated" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_order_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "order-admin-ui@test.local")
    await client.post("/api/v1/auth/register", json={"email": "order-user-ui@test.local", "password": "password123"})
    plan_id = await _create_plan(engine, "Order UI Plan")

    res = await client.get("/admin/orders")
    assert res.status_code == 200
    assert "/admin/fragments/orders/table" in res.text

    res = await client.get("/admin/fragments/orders/table")
    assert res.status_code == 200
    assert "暂无订单" in res.text

    res = await client.get("/admin/fragments/orders/assign-form")
    assert res.status_code == 200
    assert "分配订单" in res.text

    res = await client.post(
        "/admin/actions/orders/assign",
        data={
            "csrf_token": csrf,
            "email": "order-user-ui@test.local",
            "plan_id": str(plan_id),
            "period": "month_price",
            "total_amount": "500",
        },
    )
    assert res.status_code == 200
    assert "待支付" in res.text
    assert "5.00" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#orders-table"

    trade_no = await _latest_order_trade_no(engine)
    res = await client.post(f"/admin/actions/orders/{trade_no}/cancel", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "已取消" in res.text

    res = await client.post(
        "/admin/actions/orders/assign",
        data={
            "csrf_token": csrf,
            "email": "order-user-ui@test.local",
            "plan_id": str(plan_id),
            "period": "month_price",
            "total_amount": "0",
        },
    )
    assert res.status_code == 200
    trade_no = await _latest_order_trade_no(engine)

    res = await client.post(f"/admin/actions/orders/{trade_no}/paid", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "已完成" in res.text

    res = await client.post(
        "/admin/actions/orders/assign",
        data={
            "csrf_token": "wrong",
            "email": "order-user-ui@test.local",
            "plan_id": str(plan_id),
            "period": "month_price",
        },
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text


@pytest.mark.asyncio
async def test_admin_ui_notice_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "notice-admin-ui@test.local")

    res = await client.get("/admin/notices")
    assert res.status_code == 200
    assert "/admin/fragments/notices/table" in res.text

    res = await client.get("/admin/fragments/notices/table")
    assert res.status_code == 200
    assert "暂无公告" in res.text

    res = await client.get("/admin/fragments/notices/form")
    assert res.status_code == 200
    assert "创建公告" in res.text

    res = await client.post(
        "/admin/actions/notices",
        data={
            "csrf_token": csrf,
            "title": "UI Notice",
            "content": "Notice body",
            "tags": "ops",
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Notice" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#notices-table"

    notice_id = await _notice_id(engine, "UI Notice")
    res = await client.get(f"/admin/fragments/notices/form?notice_id={notice_id}")
    assert res.status_code == 200
    assert "编辑公告" in res.text

    res = await client.post(
        f"/admin/actions/notices/{notice_id}",
        data={
            "csrf_token": csrf,
            "title": "UI Notice Updated",
            "content": "Updated body",
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Notice Updated" in res.text

    res = await client.post(
        "/admin/actions/notices",
        data={"csrf_token": "wrong", "title": "Bad", "content": "Bad"},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    res = await client.post(f"/admin/actions/notices/{notice_id}/delete", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "UI Notice Updated" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_knowledge_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "knowledge-admin-ui@test.local")

    res = await client.get("/admin/knowledge")
    assert res.status_code == 200
    assert "/admin/fragments/knowledge/table" in res.text

    res = await client.get("/admin/fragments/knowledge/table")
    assert res.status_code == 200
    assert "暂无知识" in res.text

    res = await client.get("/admin/fragments/knowledge/form")
    assert res.status_code == 200
    assert "创建知识" in res.text

    res = await client.post(
        "/admin/actions/knowledge",
        data={
            "csrf_token": csrf,
            "language": "zh",
            "category": "入门",
            "title": "UI Knowledge",
            "body": "Knowledge body",
            "sort": "1",
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Knowledge" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#knowledge-table"

    knowledge_id = await _knowledge_id(engine, "UI Knowledge")
    res = await client.get(f"/admin/fragments/knowledge/form?knowledge_id={knowledge_id}")
    assert res.status_code == 200
    assert "编辑知识" in res.text

    res = await client.post(
        f"/admin/actions/knowledge/{knowledge_id}",
        data={
            "csrf_token": csrf,
            "language": "zh",
            "category": "入门",
            "title": "UI Knowledge Updated",
            "body": "Updated body",
            "sort": "2",
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Knowledge Updated" in res.text

    res = await client.post(
        "/admin/actions/knowledge",
        data={"csrf_token": "wrong", "language": "zh", "category": "x", "title": "Bad", "body": "Bad"},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    res = await client.post(f"/admin/actions/knowledge/{knowledge_id}/delete", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "UI Knowledge Updated" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_coupon_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "coupon-admin-ui@test.local")
    started_at = int(time.time()) - 60
    ended_at = int(time.time()) + 86400

    res = await client.get("/admin/coupons")
    assert res.status_code == 200
    assert "/admin/fragments/coupons/table" in res.text

    res = await client.get("/admin/fragments/coupons/table")
    assert res.status_code == 200
    assert "暂无优惠券" in res.text

    res = await client.get("/admin/fragments/coupons/form")
    assert res.status_code == 200
    assert "创建优惠券" in res.text

    res = await client.post(
        "/admin/actions/coupons",
        data={
            "csrf_token": csrf,
            "code": "UI10",
            "name": "UI Coupon",
            "type": "1",
            "value": "100",
            "started_at": str(started_at),
            "ended_at": str(ended_at),
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Coupon" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#coupons-table"

    coupon_id = await _coupon_id(engine, "UI10")
    res = await client.get(f"/admin/fragments/coupons/form?coupon_id={coupon_id}")
    assert res.status_code == 200
    assert "编辑优惠券" in res.text

    res = await client.post(
        f"/admin/actions/coupons/{coupon_id}",
        data={
            "csrf_token": csrf,
            "code": "UI20",
            "name": "UI Coupon Updated",
            "type": "2",
            "value": "20",
            "started_at": str(started_at),
            "ended_at": str(ended_at),
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Coupon Updated" in res.text

    res = await client.post(f"/admin/actions/coupons/{coupon_id}/toggle", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "停用" in res.text

    res = await client.get("/admin/fragments/coupons/generate-form")
    assert res.status_code == 200
    assert "批量生成优惠券" in res.text

    res = await client.post(
        "/admin/actions/coupons/generate",
        data={
            "csrf_token": csrf,
            "name": "Generated Coupon",
            "type": "1",
            "value": "50",
            "generate_count": "2",
            "started_at": str(started_at),
            "ended_at": str(ended_at),
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "Generated Coupon" in res.text

    res = await client.post(
        "/admin/actions/coupons",
        data={"csrf_token": "wrong", "name": "Bad", "type": "1", "value": "1"},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    res = await client.post(f"/admin/actions/coupons/{coupon_id}/delete", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "UI Coupon Updated" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_giftcard_management_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "giftcard-admin-ui@test.local")
    started_at = int(time.time()) - 60
    ended_at = int(time.time()) + 86400

    res = await client.get("/admin/giftcards")
    assert res.status_code == 200
    assert "/admin/fragments/giftcards/table" in res.text

    res = await client.get("/admin/fragments/giftcards/table")
    assert res.status_code == 200
    assert "暂无礼品卡" in res.text

    res = await client.get("/admin/fragments/giftcards/form")
    assert res.status_code == 200
    assert "创建礼品卡" in res.text

    res = await client.post(
        "/admin/actions/giftcards",
        data={
            "csrf_token": csrf,
            "code": "GIFTA",
            "name": "UI Giftcard",
            "type": "1",
            "value": "100",
            "limit_use": "1",
            "started_at": str(started_at),
            "ended_at": str(ended_at),
        },
    )
    assert res.status_code == 200
    assert "UI Giftcard" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"
    assert res.headers["hx-retarget"] == "#giftcards-table"

    giftcard_id = await _giftcard_id(engine, "GIFTA")
    res = await client.get(f"/admin/fragments/giftcards/form?giftcard_id={giftcard_id}")
    assert res.status_code == 200
    assert "编辑礼品卡" in res.text

    res = await client.post(
        f"/admin/actions/giftcards/{giftcard_id}",
        data={
            "csrf_token": csrf,
            "code": "GIFTB",
            "name": "UI Giftcard Updated",
            "type": "1",
            "value": "200",
            "limit_use": "2",
            "started_at": str(started_at),
            "ended_at": str(ended_at),
        },
    )
    assert res.status_code == 200
    assert "UI Giftcard Updated" in res.text

    res = await client.get("/admin/fragments/giftcards/generate-form")
    assert res.status_code == 200
    assert "批量生成礼品卡" in res.text

    res = await client.post(
        "/admin/actions/giftcards/generate",
        data={
            "csrf_token": csrf,
            "name": "Generated Giftcard",
            "type": "1",
            "value": "50",
            "generate_count": "2",
            "started_at": str(started_at),
            "ended_at": str(ended_at),
        },
    )
    assert res.status_code == 200
    assert "Generated Giftcard" in res.text

    res = await client.post(
        "/admin/actions/giftcards",
        data={"csrf_token": "wrong", "name": "Bad", "type": "1", "started_at": "1", "ended_at": "2"},
    )
    assert res.status_code == 200
    assert "CSRF 校验失败" in res.text

    res = await client.post(f"/admin/actions/giftcards/{giftcard_id}/delete", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "UI Giftcard Updated" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_settings_invite_ticket_server_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "settings-admin-ui@test.local")

    res = await client.get("/admin/settings")
    assert res.status_code == 200
    assert "/admin/fragments/settings/groups" in res.text
    assert "自定义配置" not in res.text
    assert "/admin/fragments/settings/table" not in res.text
    assert "/admin/fragments/settings/form" not in res.text

    res = await client.get("/admin/fragments/settings/groups?active_group=site")
    assert res.status_code == 200
    assert "应用名称" in res.text

    res = await client.post(
        "/admin/actions/settings/groups/site",
        data={"csrf_token": csrf, "_type_app_name": "str", "app_name": "Admin UI Panel"},
    )
    assert res.status_code == 200
    assert "Admin UI Panel" in res.text

    await client.post("/api/v1/auth/register", json={"email": "invite-ui-user@test.local", "password": "password123"})
    invite_user_id = await _user_id(engine, "invite-ui-user@test.local")

    res = await client.get("/admin/invite")
    assert res.status_code == 200
    assert "/admin/fragments/invite/codes" in res.text

    res = await client.post(
        "/admin/actions/invite/codes",
        data={"csrf_token": csrf, "user_id": str(invite_user_id), "code": "INVUI", "status": "0"},
    )
    assert res.status_code == 200
    assert "INVUI" in res.text
    invite_id = await _invite_id(engine, "INVUI")

    res = await client.get(f"/admin/fragments/invite/code-form?invite_id={invite_id}")
    assert res.status_code == 200
    assert "编辑邀请码" in res.text

    res = await client.post(
        f"/admin/actions/invite/codes/{invite_id}",
        data={"csrf_token": csrf, "status": "1", "pv": "3"},
    )
    assert res.status_code == 200
    assert "停用" in res.text

    user_token = await _register_user_token(client, "ticket-ui-user@test.local")
    res = await client.post(
        "/api/v1/tickets",
        json={"subject": "UI Ticket", "level": 1, "message": "Need help"},
        headers={"Authorization": user_token},
    )
    assert res.status_code == 201
    ticket_id = res.json()["data"]["ticket"]["id"]

    res = await client.get("/admin/tickets")
    assert res.status_code == 200
    assert "/admin/fragments/tickets/table" in res.text

    res = await client.get("/admin/fragments/tickets/table")
    assert res.status_code == 200
    assert "UI Ticket" in res.text

    res = await client.get(f"/admin/fragments/tickets/detail?ticket_id={ticket_id}")
    assert res.status_code == 200
    assert "Need help" in res.text

    res = await client.post(
        f"/admin/actions/tickets/{ticket_id}/reply",
        data={"csrf_token": csrf, "message": "Admin reply"},
    )
    assert res.status_code == 200
    assert "Admin reply" in res.text

    res = await client.post(
        f"/admin/actions/tickets/{ticket_id}/close",
        data={"csrf_token": csrf, "target": "detail"},
    )
    assert res.status_code == 200
    assert "已关闭" in res.text

    res = await client.get("/admin/servers")
    assert res.status_code == 200
    assert "/admin/fragments/servers/nodes/table" in res.text

    res = await client.post("/admin/actions/servers/groups", data={"csrf_token": csrf, "name": "UI Group"})
    assert res.status_code == 200
    assert "UI Group" in res.text
    group_id = await _server_group_id(engine, "UI Group")

    res = await client.post(
        "/admin/actions/servers/routes",
        data={"csrf_token": csrf, "remarks": "UI Route", "action": "block", "match": "domain:example.com"},
    )
    assert res.status_code == 200
    assert "UI Route" in res.text
    route_id = await _server_route_id(engine, "UI Route")

    res = await client.post(
        "/admin/actions/servers/nodes",
        data={
            "csrf_token": csrf,
            "group_id": str(group_id),
            "route_id": str(route_id),
            "name": "UI Node",
            "host": "node.ui.test",
            "port": "443",
            "server_port": "443",
            "rate": "1",
            "protocol": "vless",
            "tls": "1",
            "network": "tcp",
            "tls_settings": '{"server_name":"node.ui.test"}',
            "network_settings": "{}",
            "encryption_settings": "{}",
            "show": "1",
        },
    )
    assert res.status_code == 200
    assert "UI Node" in res.text
    assert res.headers["hx-trigger"] == "admin:close-modal"

    node_id = await _server_node_id(engine, "UI Node")
    res = await client.get(f"/admin/fragments/servers/nodes/form?node_id={node_id}")
    assert res.status_code == 200
    assert "编辑节点" in res.text

    res = await client.post(f"/admin/actions/servers/nodes/{node_id}/copy", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "UI Node" in res.text

    res = await client.post(f"/admin/actions/invite/codes/{invite_id}/delete", data={"csrf_token": csrf})
    assert res.status_code == 200
    assert "INVUI" not in res.text


@pytest.mark.asyncio
async def test_admin_ui_ops_pages_flow(client, engine):
    csrf = await _login_admin_ui(client, engine, "ops-admin-ui@test.local")
    await _seed_failed_job(engine)

    for path in ["/admin/dashboard", "/admin/system", "/admin/logs", "/admin/failed-jobs", "/admin/mail"]:
        res = await client.get(path)
        assert res.status_code == 200

    res = await client.get("/admin/stats", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/admin/dashboard"

    res = await client.get("/admin/fragments/dashboard/overview")
    assert res.status_code == 200
    assert "订单数" in res.text
    assert "节点流量排行" in res.text

    res = await client.get("/admin/fragments/dashboard/user-traffic?user_id=1")
    assert res.status_code == 200
    assert "用户流量" in res.text

    res = await client.get("/admin/fragments/system/status")
    assert res.status_code == 200
    assert "运行环境" in res.text

    res = await client.get("/admin/fragments/logs/table")
    assert res.status_code == 200
    assert "系统事件" in res.text

    res = await client.get("/admin/fragments/failed-jobs/table")
    assert res.status_code == 200
    assert "ui-default" in res.text

    res = await client.get("/admin/fragments/failed-jobs/detail?job_id=1")
    assert res.status_code == 200
    assert "ui_job" in res.text

    res = await client.get("/admin/fragments/mail/send-form")
    assert res.status_code == 200
    assert "发送邮件" in res.text

    res = await client.post(
        "/admin/actions/mail/send",
        data={
            "csrf_token": csrf,
            "email": "ops-target@test.local",
            "subject": "UI Mail",
            "template_name": "system_notify",
            "template_value": '{"name":"UI","content":"Hello","url":""}',
        },
    )
    assert res.status_code == 200
    assert "ops-target@test.local" in res.text



async def _promote_admin(engine, email: str) -> None:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = UserRepository(db)
        user = await repo.get_by_email(email)
        assert user is not None
        user.is_admin = True
        await repo.update(user)
        await db.commit()


async def _login_admin_ui(client, engine, email: str) -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    await _promote_admin(engine, email)
    res = await client.get("/admin/login")
    assert res.status_code == 200
    csrf = client.cookies.get("admin_csrf")
    assert csrf
    res = await client.post(
        "/admin/login",
        data={"csrf_token": csrf, "email": email, "password": "password123", "next": "/admin/dashboard"},
        follow_redirects=False,
    )
    assert res.status_code == 303
    csrf = client.cookies.get("admin_csrf")
    assert csrf
    return csrf


async def _user_id(engine, email: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = UserRepository(db)
        user = await repo.get_by_email(email)
        assert user is not None
        assert user.id is not None
        return user.id


async def _plan_id(engine, name: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = PlanRepository(db)
        plans = await repo.list_all()
        plan = next((item for item in plans if item.name == name), None)
        assert plan is not None
        assert plan.id is not None
        return plan.id


async def _payment_id(engine, name: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = PaymentRepository(db)
        payments = await repo.get_all()
        payment = next((item for item in payments if item.name == name), None)
        assert payment is not None
        assert payment.id is not None
        return payment.id


async def _create_plan(engine, name: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = PlanRepository(db)
        plan = await repo.create(
            Plan(
                name=name,
                group_id=1,
                transfer_enable=10 * 1024 * 1024,
                month_price=500,
                show=True,
            )
        )
        await db.commit()
        assert plan.id is not None
        return plan.id


async def _latest_order_trade_no(engine) -> str:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = OrderRepository(db)
        orders = await repo.get_all()
        assert orders
        latest = max(orders, key=lambda item: item.id or 0)
        return latest.trade_no


async def _notice_id(engine, title: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = NoticeRepository(db)
        notices = await repo.list_all()
        notice = next((item for item in notices if item.title == title), None)
        assert notice is not None
        assert notice.id is not None
        return notice.id


async def _knowledge_id(engine, title: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = KnowledgeRepository(db)
        items = await repo.list_all()
        knowledge = next((item for item in items if item.title == title), None)
        assert knowledge is not None
        assert knowledge.id is not None
        return knowledge.id


async def _coupon_id(engine, code: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = CouponRepository(db)
        coupon = await repo.get_by_code(code)
        assert coupon is not None
        assert coupon.id is not None
        return coupon.id


async def _giftcard_id(engine, code: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = GiftcardRepository(db)
        giftcard = await repo.get_by_code(code)
        assert giftcard is not None
        assert giftcard.id is not None
        return giftcard.id


async def _invite_id(engine, code: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        from app.repositories.invite_code import InviteCodeRepository

        repo = InviteCodeRepository(db)
        invite = await repo.get_by_code(code)
        assert invite is not None
        assert invite.id is not None
        return invite.id


async def _server_group_id(engine, name: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = ServerGroupRepository(db)
        groups = await repo.list_all()
        group = next((item for item in groups if item.name == name), None)
        assert group is not None
        assert group.id is not None
        return group.id


async def _server_route_id(engine, remarks: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = ServerRouteRepository(db)
        routes = await repo.list_all()
        route = next((item for item in routes if item.remarks == remarks), None)
        assert route is not None
        assert route.id is not None
        return route.id


async def _server_node_id(engine, name: str) -> int:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        repo = ServerV2NodeRepository(db)
        nodes = await repo.list_all()
        node = next((item for item in nodes if item.name == name), None)
        assert node is not None
        assert node.id is not None
        return node.id


async def _register_user_token(client, email: str) -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert res.status_code == 201
    return res.json()["data"]["auth_token"]


async def _seed_failed_job(engine) -> None:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(
            FailedJob(
                connection="postgresql",
                queue="ui-default",
                payload='{"job_name":"ui_job","args":[],"kwargs":{}}',
                exception="RuntimeError: failed",
                failed_at="2026-05-14 00:00:00",
            )
        )
        await db.commit()
