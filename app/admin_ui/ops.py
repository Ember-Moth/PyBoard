"""Admin 运维类 HTML 路由。"""

from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
from app.admin_ui.forms import mail_send_from_form
from app.core.deps import (
    QueueDep,
    get_auth_service,
    get_failed_job_service,
    get_log_service,
    get_mail_service,
    get_system_service,
)
from app.core.queue import PostgresQueue
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.queues.names import QUEUE_NAMES
from app.services.admin_tools import FailedJobService, LogService
from app.services.auth import AuthService
from app.services.mail import MailService
from app.services.system import SystemService

router = APIRouter()


@router.get("/stats", response_class=HTMLResponse, include_in_schema=False)
async def stats_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return RedirectResponse("/admin/dashboard", status_code=303)


@router.get("/system", response_class=HTMLResponse, include_in_schema=False)
async def system_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/system.html.j2", request, admin, "system", "系统状态")


@router.get(
    "/fragments/system/status", response_class=HTMLResponse, include_in_schema=False
)
async def system_status(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    system_service: SystemService = Depends(get_system_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    queue = await system_service.queue_stats()
    return template(
        "admin/fragments/system_status.html.j2",
        request,
        {
            "admin": admin,
            "status": await system_service.status(),
            "queue": queue,
            "workload": [
                {"name": name, "jobs": queue["queues"].get(name, 0)}
                for name in QUEUE_NAMES
            ],
        },
    )


@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/logs.html.j2", request, admin, "logs", "系统事件")


@router.get(
    "/fragments/logs/table", response_class=HTMLResponse, include_in_schema=False
)
async def logs_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    q: str | None = None,
    category: str | None = None,
    level: str | None = None,
    auth: AuthService = Depends(get_auth_service),
    log_service: LogService = Depends(get_log_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await logs_table_response(
        request,
        admin,
        log_service,
        offset,
        limit,
        q=q,
        category=category,
        level=level,
    )


@router.get(
    "/fragments/logs/detail", response_class=HTMLResponse, include_in_schema=False
)
async def log_detail(
    request: Request,
    log_id: int,
    auth: AuthService = Depends(get_auth_service),
    log_service: LogService = Depends(get_log_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    try:
        log = await log_service.get_log(log_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return template(
        "admin/fragments/log_detail.html.j2", request, {"admin": admin, "log": log}
    )


@router.post(
    "/actions/logs/{log_id}/delete",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def delete_log_action(
    log_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    log_service: LogService = Depends(get_log_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await log_service.delete_log(log_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await logs_table_response(
        request,
        admin,
        log_service,
        int_or_none(form.get("offset")) or 0,
        int_or_none(form.get("limit")) or 50,
        q=form.get("q"),
        category=form.get("category"),
        level=form.get("level"),
    )


@router.get("/failed-jobs", response_class=HTMLResponse, include_in_schema=False)
async def failed_jobs_page(
    request: Request, auth: AuthService = Depends(get_auth_service)
):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page(
        "admin/pages/failed_jobs.html.j2", request, admin, "failed_jobs", "失败任务"
    )


@router.get(
    "/fragments/failed-jobs/table", response_class=HTMLResponse, include_in_schema=False
)
async def failed_jobs_table(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    job_service: FailedJobService = Depends(get_failed_job_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await failed_jobs_table_response(request, admin, job_service, offset, limit)


@router.get(
    "/fragments/failed-jobs/detail",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def failed_job_detail(
    request: Request,
    job_id: int,
    auth: AuthService = Depends(get_auth_service),
    job_service: FailedJobService = Depends(get_failed_job_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    try:
        job = await job_service.get_job(job_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return template(
        "admin/fragments/failed_job_detail.html.j2",
        request,
        {"admin": admin, "job": job},
    )


@router.post(
    "/actions/failed-jobs/{job_id}/retry",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def retry_failed_job_action(
    job_id: int,
    request: Request,
    queue: PostgresQueue = QueueDep,
    auth: AuthService = Depends(get_auth_service),
    job_service: FailedJobService = Depends(get_failed_job_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await job_service.retry_job(job_id, queue)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await failed_jobs_table_response(request, admin, job_service)


@router.post(
    "/actions/failed-jobs/{job_id}/delete",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def delete_failed_job_action(
    job_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    job_service: FailedJobService = Depends(get_failed_job_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await job_service.delete_job(job_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await failed_jobs_table_response(
        request,
        admin,
        job_service,
        int_or_none(form.get("offset")) or 0,
        int_or_none(form.get("limit")) or 50,
    )


@router.get("/mail", response_class=HTMLResponse, include_in_schema=False)
async def mail_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/mail.html.j2", request, admin, "mail", "邮件管理")


@router.get(
    "/fragments/mail/logs", response_class=HTMLResponse, include_in_schema=False
)
async def mail_logs(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    auth: AuthService = Depends(get_auth_service),
    mail_service: MailService = Depends(get_mail_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await mail_logs_response(request, admin, mail_service, offset, limit)


@router.get(
    "/fragments/mail/send-form", response_class=HTMLResponse, include_in_schema=False
)
async def mail_send_form(
    request: Request, auth: AuthService = Depends(get_auth_service)
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return template(
        "admin/fragments/mail_send_form.html.j2",
        request,
        {"admin": admin, "templates": _mail_templates()},
    )


@router.get(
    "/fragments/mail/log-detail", response_class=HTMLResponse, include_in_schema=False
)
async def mail_log_detail(
    request: Request,
    log_id: int,
    auth: AuthService = Depends(get_auth_service),
    mail_service: MailService = Depends(get_mail_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    try:
        log = await mail_service.get_log(log_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return template(
        "admin/fragments/mail_log_detail.html.j2", request, {"admin": admin, "log": log}
    )


@router.post("/actions/mail/send", response_class=HTMLResponse, include_in_schema=False)
async def send_mail_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    mail_service: MailService = Depends(get_mail_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await mail_service.send(mail_send_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await mail_logs_response(request, admin, mail_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#mail-logs"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


async def logs_table_response(
    request: Request,
    admin: UserRead,
    log_service: LogService,
    offset: int = 0,
    limit: int = 50,
    *,
    q: str | None = None,
    category: str | None = None,
    level: str | None = None,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    filters = {
        "q": (q or "").strip(),
        "category": (category or "").strip(),
        "level": (level or "").strip(),
    }
    return template(
        "admin/fragments/logs_table.html.j2",
        request,
        {
            "admin": admin,
            "logs": await log_service.list_logs(
                offset,
                limit,
                q=filters["q"] or None,
                category=filters["category"] or None,
                level=filters["level"] or None,
            ),
            "offset": offset,
            "limit": limit,
            "filters": filters,
        },
    )


async def failed_jobs_table_response(
    request: Request,
    admin: UserRead,
    job_service: FailedJobService,
    offset: int = 0,
    limit: int = 50,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return template(
        "admin/fragments/failed_jobs_table.html.j2",
        request,
        {
            "admin": admin,
            "jobs": await job_service.list_jobs(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )


async def mail_logs_response(
    request: Request,
    admin: UserRead,
    mail_service: MailService,
    offset: int = 0,
    limit: int = 50,
):
    offset = max(offset, 0)
    limit = min(max(limit, 1), 200)
    return template(
        "admin/fragments/mail_logs_table.html.j2",
        request,
        {
            "admin": admin,
            "logs": await mail_service.list_logs(offset, limit),
            "offset": offset,
            "limit": limit,
        },
    )


def _mail_templates() -> list[str]:
    path = Path("app/templates/mail")
    return sorted(item.stem for item in path.glob("*.html") if item.is_file())
