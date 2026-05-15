"""Admin 订单管理路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.admin_ui.deps import (
    action_error,
    current_admin,
    form_data,
    page,
    redirect_to_login,
    template,
    unauthorized_fragment,
    valid_csrf,
    validation_error_message,
)
from app.admin_ui.forms import order_assign_from_form
from app.core.deps import get_auth_service, get_order_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.order import OrderService

router = APIRouter()


@router.get("/orders", response_class=HTMLResponse, include_in_schema=False)
async def orders_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/orders.html.j2", request, user, "orders", "订单管理")


@router.get("/fragments/orders/table", response_class=HTMLResponse, include_in_schema=False)
async def orders_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    order_service: OrderService = Depends(get_order_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return await orders_table_response(request, admin, order_service, offset, limit)


@router.get("/fragments/orders/assign-form", response_class=HTMLResponse, include_in_schema=False)
async def order_assign_form(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return template("admin/fragments/order_assign_form.html.j2", request, {"admin": admin})


@router.post("/actions/orders/assign", response_class=HTMLResponse, include_in_schema=False)
async def assign_order_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    order_service: OrderService = Depends(get_order_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await order_service.admin_assign_order(order_assign_from_form(form), actor_id=admin.id)
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await orders_table_response(request, admin, order_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#orders-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/orders/{trade_no}/paid", response_class=HTMLResponse, include_in_schema=False)
async def mark_order_paid_action(
    trade_no: str,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    order_service: OrderService = Depends(get_order_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await order_service.admin_mark_paid(trade_no, actor_id=admin.id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await orders_table_response(request, admin, order_service)


@router.post("/actions/orders/{trade_no}/cancel", response_class=HTMLResponse, include_in_schema=False)
async def cancel_order_action(
    trade_no: str,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    order_service: OrderService = Depends(get_order_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await order_service.admin_cancel_order(trade_no, actor_id=admin.id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await orders_table_response(request, admin, order_service)


async def orders_table_response(
    request: Request,
    admin: UserRead,
    order_service: OrderService,
    offset: int = 0,
    limit: int = 50,
):
    return template(
        "admin/fragments/orders_table.html.j2",
        request,
        {
            "admin": admin,
            "orders": await order_service.list_orders(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )
