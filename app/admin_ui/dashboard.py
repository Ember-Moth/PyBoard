"""Admin 仪表盘路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.admin_ui.deps import current_admin, page, redirect_to_login, template, unauthorized_fragment
from app.core.deps import get_auth_service, get_stat_service, get_system_service
from app.services.auth import AuthService
from app.services.stat import StatService
from app.services.system import SystemService

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/dashboard.html.j2", request, user, "dashboard", "仪表盘")


@router.get("/fragments/dashboard/overview", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_overview(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    stat_service: StatService = Depends(get_stat_service),
    system_service: SystemService = Depends(get_system_service),
):
    user = await current_admin(request, auth)
    if user is None:
        return unauthorized_fragment()
    return template(
        "admin/fragments/dashboard_overview.html.j2",
        request,
        {
            "admin": user,
            "overview": await stat_service.overview(),
            "orders": await stat_service.order_series(30),
            "server_rank": await stat_service.server_rank("today", 15),
            "user_rank": await stat_service.user_rank("today", 30),
            "system": await system_service.status(),
            "queue": await system_service.queue_stats(),
        },
    )


@router.get("/fragments/dashboard/user-traffic", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_user_traffic(
    request: Request,
    user_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    stat_service: StatService = Depends(get_stat_service),
):
    user = await current_admin(request, auth)
    if user is None:
        return unauthorized_fragment()
    traffic = await stat_service.user_traffic_log(user_id, 30) if user_id else []
    return template(
        "admin/fragments/stats_user_traffic.html.j2",
        request,
        {
            "admin": user,
            "user_id": user_id or "",
            "traffic": traffic,
            "fragment_path": "/admin/fragments/dashboard/user-traffic",
            "fragment_target": "#dashboard-user-traffic",
        },
    )
