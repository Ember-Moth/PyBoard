"""Admin 套餐管理路由。"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.admin_ui.deps import (
    action_error,
    current_admin,
    form_data,
    page,
    redirect_to_login,
    template,
    unauthorized_fragment,
    valid_csrf,
    validation_error_message,
)
from app.admin_ui.forms import plan_create_from_form, plan_update_from_form
from app.core.deps import get_auth_service, get_plan_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.plan import PlanService

router = APIRouter()


@router.get("/plans", response_class=HTMLResponse, include_in_schema=False)
async def plans_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/plans.html.j2", request, user, "plans", "套餐管理")


@router.get("/fragments/plans/table", response_class=HTMLResponse, include_in_schema=False)
async def plans_table(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    plan_service: PlanService = Depends(get_plan_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await plans_table_response(request, admin, plan_service)


@router.get("/fragments/plans/form", response_class=HTMLResponse, include_in_schema=False)
async def plan_form(
    request: Request,
    plan_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    plan_service: PlanService = Depends(get_plan_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    plan = await plan_service.get(plan_id) if plan_id else None
    return template("admin/fragments/plan_form.html.j2", request, {"admin": admin, "plan": plan})


@router.post("/actions/plans", response_class=HTMLResponse, include_in_schema=False)
async def create_plan_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    plan_service: PlanService = Depends(get_plan_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await plan_service.create(plan_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await plans_table_response(request, admin, plan_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#plans-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/plans/{plan_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_plan_action(
    plan_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    plan_service: PlanService = Depends(get_plan_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await plan_service.update(plan_id, plan_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await plans_table_response(request, admin, plan_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#plans-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/plans/{plan_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_plan_action(
    plan_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    plan_service: PlanService = Depends(get_plan_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await plan_service.delete(plan_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await plans_table_response(request, admin, plan_service)


async def plans_table_response(request: Request, admin: UserRead, plan_service: PlanService):
    return template(
        "admin/fragments/plans_table.html.j2",
        request,
        {"admin": admin, "plans": await plan_service.list_all()},
    )
