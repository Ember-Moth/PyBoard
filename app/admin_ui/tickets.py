"""Admin 工单 HTML 路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.admin_ui.deps import (
    action_error,
    blank_none,
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
from app.admin_ui.forms import ticket_reply_from_form
from app.core.deps import get_auth_service, get_ticket_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.ticket import TicketService

router = APIRouter()


@router.get("/tickets", response_class=HTMLResponse, include_in_schema=False)
async def tickets_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/tickets.html.j2", request, admin, "tickets", "工单管理")


@router.get("/fragments/tickets/table", response_class=HTMLResponse, include_in_schema=False)
async def tickets_table(
    request: Request,
    page_no: int = 1,
    size: int = 50,
    status: int | None = None,
    reply_status: int | None = None,
    email: str | None = None,
    auth: AuthService = Depends(get_auth_service),
    ticket_service: TicketService = Depends(get_ticket_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await tickets_table_response(
        request,
        admin,
        ticket_service,
        page_no,
        size,
        status=status,
        reply_status=reply_status,
        email=blank_none(email),
    )


@router.get("/fragments/tickets/detail", response_class=HTMLResponse, include_in_schema=False)
async def ticket_detail(
    request: Request,
    ticket_id: int,
    auth: AuthService = Depends(get_auth_service),
    ticket_service: TicketService = Depends(get_ticket_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    try:
        detail = await ticket_service.get_admin_ticket(ticket_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return template("admin/fragments/ticket_detail.html.j2", request, {"admin": admin, "detail": detail})


@router.post("/actions/tickets/{ticket_id}/reply", response_class=HTMLResponse, include_in_schema=False)
async def reply_ticket_action(
    ticket_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    ticket_service: TicketService = Depends(get_ticket_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        detail = await ticket_service.reply_admin_ticket(admin.id, ticket_id, ticket_reply_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    return template("admin/fragments/ticket_detail.html.j2", request, {"admin": admin, "detail": detail})


@router.post("/actions/tickets/{ticket_id}/close", response_class=HTMLResponse, include_in_schema=False)
async def close_ticket_action(
    ticket_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    ticket_service: TicketService = Depends(get_ticket_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await ticket_service.close_admin_ticket(ticket_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    if form.get("target") == "detail":
        detail = await ticket_service.get_admin_ticket(ticket_id)
        return template("admin/fragments/ticket_detail.html.j2", request, {"admin": admin, "detail": detail})
    return await tickets_table_response(
        request,
        admin,
        ticket_service,
        int_or_none(form.get("page_no")) or 1,
        int_or_none(form.get("size")) or 50,
        status=int_or_none(form.get("status")),
        reply_status=int_or_none(form.get("reply_status")),
        email=blank_none(form.get("email")),
    )


async def tickets_table_response(
    request: Request,
    admin: UserRead,
    ticket_service: TicketService,
    page_no: int = 1,
    size: int = 50,
    *,
    status: int | None = None,
    reply_status: int | None = None,
    email: str | None = None,
):
    page_no = max(page_no, 1)
    size = min(max(size, 1), 200)
    data = await ticket_service.list_admin_tickets(
        page_no,
        size,
        status=status,
        reply_status=reply_status,
        email=email,
    )
    return template(
        "admin/fragments/tickets_table.html.j2",
        request,
        {
            "admin": admin,
            "tickets": data.items,
            "total": data.total,
            "page_no": data.page,
            "size": data.size,
            "status": status if status is not None else "",
            "reply_status": reply_status if reply_status is not None else "",
            "email": email or "",
        },
    )
