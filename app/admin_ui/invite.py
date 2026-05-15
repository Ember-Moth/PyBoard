"""Admin 邀请返利 HTML 路由。"""

from typing import Any

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
from app.admin_ui.forms import invite_code_create_from_form, invite_code_update_from_form
from app.core.deps import get_auth_service, get_invite_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.commission import InviteService

router = APIRouter()


@router.get("/invite", response_class=HTMLResponse, include_in_schema=False)
async def invite_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/invite.html.j2", request, admin, "invite", "邀请返利")


@router.get("/fragments/invite/codes", response_class=HTMLResponse, include_in_schema=False)
async def invite_codes_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    invite_service: InviteService = Depends(get_invite_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await invite_codes_response(request, admin, invite_service, offset, limit)


@router.get("/fragments/invite/commission-logs", response_class=HTMLResponse, include_in_schema=False)
async def commission_logs_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    invite_service: InviteService = Depends(get_invite_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await commission_logs_response(request, admin, invite_service, offset, limit)


@router.get("/fragments/invite/code-form", response_class=HTMLResponse, include_in_schema=False)
async def invite_code_form(
    request: Request,
    invite_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    invite_service: InviteService = Depends(get_invite_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    code = await _find_invite_code(invite_service, invite_id) if invite_id else None
    return template("admin/fragments/invite_code_form.html.j2", request, {"admin": admin, "code": code})


@router.post("/actions/invite/codes", response_class=HTMLResponse, include_in_schema=False)
async def create_invite_code_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    invite_service: InviteService = Depends(get_invite_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await invite_service.admin_create_invite_code(invite_code_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await invite_codes_response(request, admin, invite_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#invite-codes-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/invite/codes/{invite_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_invite_code_action(
    invite_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    invite_service: InviteService = Depends(get_invite_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await invite_service.admin_update_invite_code(invite_id, invite_code_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await invite_codes_response(request, admin, invite_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#invite-codes-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/invite/codes/{invite_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_invite_code_action(
    invite_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    invite_service: InviteService = Depends(get_invite_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await invite_service.admin_delete_invite_code(invite_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await invite_codes_response(
        request,
        admin,
        invite_service,
        int_or_none(form.get("offset")) or 0,
        int_or_none(form.get("limit")) or 50,
    )


async def invite_codes_response(
    request: Request,
    admin: UserRead,
    invite_service: InviteService,
    offset: int = 0,
    limit: int = 50,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return template(
        "admin/fragments/invite_codes_table.html.j2",
        request,
        {
            "admin": admin,
            "codes": await invite_service.admin_list_invite_codes(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )


async def commission_logs_response(
    request: Request,
    admin: UserRead,
    invite_service: InviteService,
    offset: int = 0,
    limit: int = 50,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return template(
        "admin/fragments/commission_logs_table.html.j2",
        request,
        {
            "admin": admin,
            "logs": await invite_service.admin_list_commission_logs(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )


async def _find_invite_code(invite_service: InviteService, invite_id: int | None) -> Any | None:
    if invite_id is None:
        return None
    for code in await invite_service.admin_list_invite_codes(0, 200):
        if code.id == invite_id:
            return code
    return None
