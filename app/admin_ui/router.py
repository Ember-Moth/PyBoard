"""Admin HTML UI 路由聚合。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.admin_ui import (
    auth,
    coupons,
    dashboard,
    giftcards,
    invite,
    knowledge,
    notices,
    ops,
    orders,
    payments,
    plans,
    servers,
    settings,
    tickets,
    users,
)
from app.admin_ui.deps import current_admin
from app.core.deps import get_auth_service
from app.services.auth import AuthService

router = APIRouter(prefix="/admin", tags=["Admin UI"])


@router.get("", include_in_schema=False)
async def admin_index(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth_service)
    if user is None:
        return RedirectResponse("/admin/login", status_code=303)
    return RedirectResponse("/admin/dashboard", status_code=303)


router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(users.router)
router.include_router(notices.router)
router.include_router(knowledge.router)
router.include_router(plans.router)
router.include_router(payments.router)
router.include_router(orders.router)
router.include_router(coupons.router)
router.include_router(giftcards.router)
router.include_router(settings.router)
router.include_router(invite.router)
router.include_router(tickets.router)
router.include_router(servers.router)
router.include_router(ops.router)
