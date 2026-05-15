"""Admin 礼品卡管理路由。"""

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
from app.admin_ui.forms import giftcard_create_from_form, giftcard_generate_from_form, giftcard_update_from_form
from app.core.deps import get_auth_service, get_giftcard_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.giftcard import GiftcardService

router = APIRouter()


@router.get("/giftcards", response_class=HTMLResponse, include_in_schema=False)
async def giftcards_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/giftcards.html.j2", request, user, "giftcards", "礼品卡管理")


@router.get("/fragments/giftcards/table", response_class=HTMLResponse, include_in_schema=False)
async def giftcards_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    giftcard_service: GiftcardService = Depends(get_giftcard_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await giftcards_table_response(request, admin, giftcard_service, offset, limit)


@router.get("/fragments/giftcards/form", response_class=HTMLResponse, include_in_schema=False)
async def giftcard_form(
    request: Request,
    giftcard_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    giftcard_service: GiftcardService = Depends(get_giftcard_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    giftcard = await giftcard_service.get(giftcard_id) if giftcard_id else None
    return template("admin/fragments/giftcard_form.html.j2", request, {"admin": admin, "giftcard": giftcard})


@router.get("/fragments/giftcards/generate-form", response_class=HTMLResponse, include_in_schema=False)
async def giftcard_generate_form(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return template("admin/fragments/giftcard_generate_form.html.j2", request, {"admin": admin})


@router.post("/actions/giftcards", response_class=HTMLResponse, include_in_schema=False)
async def create_giftcard_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    giftcard_service: GiftcardService = Depends(get_giftcard_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await giftcard_service.create(giftcard_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await giftcards_table_response(request, admin, giftcard_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#giftcards-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/giftcards/generate", response_class=HTMLResponse, include_in_schema=False)
async def generate_giftcard_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    giftcard_service: GiftcardService = Depends(get_giftcard_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await giftcard_service.generate(giftcard_generate_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await giftcards_table_response(request, admin, giftcard_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#giftcards-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/giftcards/{giftcard_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_giftcard_action(
    giftcard_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    giftcard_service: GiftcardService = Depends(get_giftcard_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await giftcard_service.update(giftcard_id, giftcard_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await giftcards_table_response(request, admin, giftcard_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#giftcards-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/giftcards/{giftcard_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_giftcard_action(
    giftcard_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    giftcard_service: GiftcardService = Depends(get_giftcard_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await giftcard_service.delete(giftcard_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await giftcards_table_response(
        request,
        admin,
        giftcard_service,
        int_or_none(form.get("offset")) or 0,
        int_or_none(form.get("limit")) or 50,
    )


async def giftcards_table_response(
    request: Request,
    admin: UserRead,
    giftcard_service: GiftcardService,
    offset: int = 0,
    limit: int = 50,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return template(
        "admin/fragments/giftcards_table.html.j2",
        request,
        {
            "admin": admin,
            "giftcards": await giftcard_service.list_all(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )
