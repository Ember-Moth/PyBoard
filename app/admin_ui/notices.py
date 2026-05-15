"""Admin 公告管理路由。"""

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
from app.admin_ui.forms import notice_create_from_form, notice_update_from_form
from app.core.deps import get_auth_service, get_notice_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.notice import NoticeService

router = APIRouter()


@router.get("/notices", response_class=HTMLResponse, include_in_schema=False)
async def notices_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/notices.html.j2", request, user, "notices", "公告管理")


@router.get("/fragments/notices/table", response_class=HTMLResponse, include_in_schema=False)
async def notices_table(
    request: Request,
    page_no: int = 1,
    size: int = 20,
    auth: AuthService = Depends(get_auth_service),
    notice_service: NoticeService = Depends(get_notice_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await notices_table_response(request, admin, notice_service, page_no, size)


@router.get("/fragments/notices/form", response_class=HTMLResponse, include_in_schema=False)
async def notice_form(
    request: Request,
    notice_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    notice_service: NoticeService = Depends(get_notice_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    notice = await notice_service.get(notice_id) if notice_id else None
    return template("admin/fragments/notice_form.html.j2", request, {"admin": admin, "notice": notice})


@router.post("/actions/notices", response_class=HTMLResponse, include_in_schema=False)
async def create_notice_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    notice_service: NoticeService = Depends(get_notice_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await notice_service.create(notice_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await notices_table_response(request, admin, notice_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#notices-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/notices/{notice_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_notice_action(
    notice_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    notice_service: NoticeService = Depends(get_notice_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await notice_service.update(notice_id, notice_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await notices_table_response(request, admin, notice_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#notices-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/notices/{notice_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_notice_action(
    notice_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    notice_service: NoticeService = Depends(get_notice_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await notice_service.delete(notice_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await notices_table_response(request, admin, notice_service, int_or_none(form.get("page_no")) or 1)


async def notices_table_response(
    request: Request,
    admin: UserRead,
    notice_service: NoticeService,
    page_no: int = 1,
    size: int = 20,
):
    page_no = max(page_no, 1)
    size = min(max(size, 1), 100)
    data = await notice_service.list_all(page_no, size)
    return template("admin/fragments/notices_table.html.j2", request, {"admin": admin, "data": data})
