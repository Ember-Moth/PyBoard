"""Admin 知识库管理路由。"""

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
from app.admin_ui.forms import knowledge_create_from_form, knowledge_update_from_form
from app.core.deps import get_auth_service, get_knowledge_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.knowledge import KnowledgeService

router = APIRouter()


@router.get("/knowledge", response_class=HTMLResponse, include_in_schema=False)
async def knowledge_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is None:
        return redirect_to_login(request)
    return page("admin/pages/knowledge.html.j2", request, user, "knowledge", "知识库管理")


@router.get("/fragments/knowledge/table", response_class=HTMLResponse, include_in_schema=False)
async def knowledge_table(
    request: Request,
    page_no: int = 1,
    size: int = 20,
    auth: AuthService = Depends(get_auth_service),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await knowledge_table_response(request, admin, knowledge_service, page_no, size)


@router.get("/fragments/knowledge/form", response_class=HTMLResponse, include_in_schema=False)
async def knowledge_form(
    request: Request,
    knowledge_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    knowledge = await knowledge_service.get(knowledge_id) if knowledge_id else None
    return template("admin/fragments/knowledge_form.html.j2", request, {"admin": admin, "knowledge": knowledge})


@router.post("/actions/knowledge", response_class=HTMLResponse, include_in_schema=False)
async def create_knowledge_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await knowledge_service.create(knowledge_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await knowledge_table_response(request, admin, knowledge_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#knowledge-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/knowledge/{knowledge_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_knowledge_action(
    knowledge_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await knowledge_service.update(knowledge_id, knowledge_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await knowledge_table_response(request, admin, knowledge_service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#knowledge-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/knowledge/{knowledge_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_knowledge_action(
    knowledge_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await knowledge_service.delete(knowledge_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await knowledge_table_response(request, admin, knowledge_service, int_or_none(form.get("page_no")) or 1)


async def knowledge_table_response(
    request: Request,
    admin: UserRead,
    knowledge_service: KnowledgeService,
    page_no: int = 1,
    size: int = 20,
):
    page_no = max(page_no, 1)
    size = min(max(size, 1), 100)
    data = await knowledge_service.list_all(page_no, size)
    return template("admin/fragments/knowledge_table.html.j2", request, {"admin": admin, "data": data})
