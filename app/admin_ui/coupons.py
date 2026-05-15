"""Admin 优惠券管理路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.admin_ui.deps import (
    action_error,
    current_admin,
    form_data,
    int_or_none,
    page,
    redirect_to_login,
    template,
    unauthorized_fragment,
    valid_csrf,
    validation_error_message,
)
from app.admin_ui.forms import coupon_create_from_form, coupon_generate_from_form, coupon_update_from_form
from app.core.deps import get_auth_service, get_coupon_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.coupon import CouponService

router = APIRouter()


@router.get("/coupons", response_class=HTMLResponse, include_in_schema=False)
async def coupons_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/coupons.html.j2", request, user, "coupons", "优惠券管理")


@router.get("/fragments/coupons/table", response_class=HTMLResponse, include_in_schema=False)
async def coupons_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await coupons_table_response(request, admin, coupon_service, offset, limit)


@router.get("/fragments/coupons/form", response_class=HTMLResponse, include_in_schema=False)
async def coupon_form(
    request: Request,
    coupon_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    coupon = await coupon_service.get(coupon_id) if coupon_id else None
    return template("admin/fragments/coupon_form.html.j2", request, {"admin": admin, "coupon": coupon})


@router.get("/fragments/coupons/generate-form", response_class=HTMLResponse, include_in_schema=False)
async def coupon_generate_form(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return template("admin/fragments/coupon_generate_form.html.j2", request, {"admin": admin})


@router.post("/actions/coupons", response_class=HTMLResponse, include_in_schema=False)
async def create_coupon_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await coupon_service.create(coupon_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await coupons_table_response(request, admin, coupon_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#coupons-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/coupons/generate", response_class=HTMLResponse, include_in_schema=False)
async def generate_coupon_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await coupon_service.generate(coupon_generate_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await coupons_table_response(request, admin, coupon_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#coupons-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/coupons/{coupon_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_coupon_action(
    coupon_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await coupon_service.update(coupon_id, coupon_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await coupons_table_response(request, admin, coupon_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#coupons-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/coupons/{coupon_id}/toggle", response_class=HTMLResponse, include_in_schema=False)
async def toggle_coupon_action(
    coupon_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await coupon_service.toggle_show(coupon_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await coupons_table_response(
        request,
        admin,
        coupon_service,
        int_or_none(form.get("offset")) or 0,
        int_or_none(form.get("limit")) or 50,
    )


@router.post("/actions/coupons/{coupon_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_coupon_action(
    coupon_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    coupon_service: CouponService = Depends(get_coupon_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await coupon_service.delete(coupon_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await coupons_table_response(
        request,
        admin,
        coupon_service,
        int_or_none(form.get("offset")) or 0,
        int_or_none(form.get("limit")) or 50,
    )


async def coupons_table_response(
    request: Request,
    admin: UserRead,
    coupon_service: CouponService,
    offset: int = 0,
    limit: int = 50,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return template(
        "admin/fragments/coupons_table.html.j2",
        request,
        {
            "admin": admin,
            "coupons": await coupon_service.list_all(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )
