"""Admin 用户管理路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.admin_ui.deps import (
    action_error,
    as_bool,
    blank_none,
    current_admin,
    datetime_or_none,
    filters_from_request,
    form_data,
    int_or_none,
    page,
    redirect_to_login,
    template,
    unauthorized_fragment,
    valid_csrf,
    validation_error_message,
)
from app.admin_ui.forms import user_update_from_form
from app.core.deps import get_auth_service, get_user_service
from app.core.exceptions import AppException
from app.models.user.dto import AdminUserBan, AdminUserGenerate, UserCreate, UserRead
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter()


@router.get("/users", response_class=HTMLResponse, include_in_schema=False)
async def users_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/users.html.j2", request, user, "users", "用户管理")


@router.get("/fragments/users/table", response_class=HTMLResponse, include_in_schema=False)
async def users_table(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    q: str | None = None,
    status: str | None = None,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    offset = max(offset, 0)
    limit = min(max(limit, 1), 100)
    q = blank_none(q)
    status = blank_none(status)
    users = await user_service.list_users(offset, limit, q, status)
    return template(
        "admin/fragments/users_table.html.j2",
        request,
        {"admin": admin, "users": users, "offset": offset, "limit": limit, "q": q or "", "status": status or ""},
    )


@router.get("/fragments/users/form", response_class=HTMLResponse, include_in_schema=False)
async def user_form(
    request: Request,
    user_id: int,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    user = await user_service.get_user(user_id)
    return template(
        "admin/fragments/user_form.html.j2",
        request,
        {"admin": admin, "user": user, "filters": filters_from_request(request)},
    )


@router.get("/fragments/users/create-form", response_class=HTMLResponse, include_in_schema=False)
async def user_create_form(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return template(
        "admin/fragments/user_create_form.html.j2",
        request,
        {"admin": admin, "filters": filters_from_request(request)},
    )


@router.get("/fragments/users/generate-form", response_class=HTMLResponse, include_in_schema=False)
async def user_generate_form(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return template(
        "admin/fragments/user_generate_form.html.j2",
        request,
        {"admin": admin, "filters": filters_from_request(request)},
    )


@router.post("/actions/users", response_class=HTMLResponse, include_in_schema=False)
async def create_user_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await user_service.create_user(
            UserCreate(email=str(form.get("email") or ""), password=str(form.get("password") or ""))
        )
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await users_table_response(request, admin, user_service, form)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#users-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/users/generate", response_class=HTMLResponse, include_in_schema=False)
async def generate_users_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await user_service.admin_generate_users(
            AdminUserGenerate(
                email_prefix=blank_none(form.get("email_prefix")),
                email_suffix=str(form.get("email_suffix") or ""),
                password=blank_none(form.get("password")),
                plan_id=int_or_none(form.get("plan_id")),
                expired_at=datetime_or_none(form.get("expired_at")),
                generate_count=int_or_none(form.get("generate_count")),
            )
        )
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await users_table_response(request, admin, user_service, form)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#users-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/users/{user_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_user_action(
    user_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await user_service.update_user(user_id, user_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await users_table_response(request, admin, user_service, form)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#users-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/users/{user_id}/ban", response_class=HTMLResponse, include_in_schema=False)
async def ban_user_action(
    user_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    await user_service.admin_set_banned(user_id, AdminUserBan(banned=as_bool(form.get("banned"))))
    return await users_table_response(request, admin, user_service, form)


@router.post("/actions/users/{user_id}/reset-security", response_class=HTMLResponse, include_in_schema=False)
async def reset_user_security_action(
    user_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    await user_service.admin_reset_security(user_id)
    return await users_table_response(request, admin, user_service, form)


@router.post("/actions/users/{user_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_user_action(
    user_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await user_service.delete_user(user_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await users_table_response(request, admin, user_service, form)


async def users_table_response(
    request: Request,
    admin: UserRead,
    user_service: UserService,
    form: dict[str, str] | None = None,
):
    filters = filters_from_request(request, form)
    offset = max(int_or_none(filters.get("offset")) or 0, 0)
    limit = min(max(int_or_none(filters.get("limit")) or 20, 1), 100)
    q = blank_none(filters.get("q"))
    status = blank_none(filters.get("status"))
    return template(
        "admin/fragments/users_table.html.j2",
        request,
        {
            "admin": admin,
            "users": await user_service.list_users(offset, limit, q, status),
            "offset": offset,
            "limit": limit,
            "q": q or "",
            "status": status or "",
        },
    )
