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
            "system": await system_service.status(),
            "queue": await system_service.queue_stats(),
        },
    )
