"""Admin 支付方式管理路由。"""

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
from app.admin_ui.forms import payment_create_from_form, payment_update_from_form
from app.core.deps import get_auth_service, get_payment_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.payment import PaymentService

router = APIRouter()


@router.get("/payments", response_class=HTMLResponse, include_in_schema=False)
async def payments_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/payments.html.j2", request, user, "payments", "支付管理")


@router.get("/fragments/payments/table", response_class=HTMLResponse, include_in_schema=False)
async def payments_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    payment_service: PaymentService = Depends(get_payment_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return await payments_table_response(request, admin, payment_service, offset, limit)


@router.get("/fragments/payments/form", response_class=HTMLResponse, include_in_schema=False)
async def payment_form(
    request: Request,
    payment_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    payment_service: PaymentService = Depends(get_payment_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    payment = await payment_service.get_payment(payment_id) if payment_id else None
    return template(
        "admin/fragments/payment_form.html.j2",
        request,
        {"admin": admin, "payment": payment, "gateways": payment_service.list_gateways()},
    )


@router.post("/actions/payments", response_class=HTMLResponse, include_in_schema=False)
async def create_payment_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    payment_service: PaymentService = Depends(get_payment_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await payment_service.create_payment(payment_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await payments_table_response(request, admin, payment_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#payments-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/payments/{payment_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_payment_action(
    payment_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    payment_service: PaymentService = Depends(get_payment_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await payment_service.update_payment(payment_id, payment_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await payments_table_response(request, admin, payment_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#payments-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/payments/{payment_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_payment_action(
    payment_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    payment_service: PaymentService = Depends(get_payment_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await payment_service.delete_payment(payment_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await payments_table_response(request, admin, payment_service)


async def payments_table_response(
    request: Request,
    admin: UserRead,
    payment_service: PaymentService,
    offset: int = 0,
    limit: int = 50,
):
    return template(
        "admin/fragments/payments_table.html.j2",
        request,
        {
            "admin": admin,
            "payments": await payment_service.list_payments(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )
