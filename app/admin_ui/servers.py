"""Admin 节点 HTML 路由。"""

from typing import Any

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
from app.admin_ui.forms import (
    server_group_create_from_form,
    server_group_update_from_form,
    server_node_create_from_form,
    server_node_update_from_form,
    server_route_create_from_form,
    server_route_update_from_form,
)
from app.core.deps import get_auth_service, get_server_admin_service
from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService
from app.services.server_admin import ServerAdminService

router = APIRouter()

PROTOCOLS = ["shadowsocks", "vmess", "vless", "trojan", "tuic", "hysteria2", "hysteria", "anytls"]
NETWORKS = ["tcp", "ws", "grpc", "http", "httpupgrade", "xhttp"]
ROUTE_ACTIONS = ["block", "block_ip", "block_port", "protocol", "dns", "route", "route_ip", "default_out"]


@router.get("/servers", response_class=HTMLResponse, include_in_schema=False)
async def servers_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    admin = await current_admin(request, auth)
    if admin is None:
        return redirect_to_login(request)
    return page("admin/pages/servers.html.j2", request, admin, "servers", "节点管理")


@router.get("/fragments/servers/groups/table", response_class=HTMLResponse, include_in_schema=False)
async def server_groups_table(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await server_groups_response(request, admin, service)


@router.get("/fragments/servers/groups/form", response_class=HTMLResponse, include_in_schema=False)
async def server_group_form(
    request: Request,
    group_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    group = await _find_by_id(await service.list_groups(), group_id)
    return template("admin/fragments/server_group_form.html.j2", request, {"admin": admin, "group": group})


@router.post("/actions/servers/groups", response_class=HTMLResponse, include_in_schema=False)
async def create_server_group_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.create_group(server_group_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await server_groups_response(request, admin, service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#server-groups-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/servers/groups/{group_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_server_group_action(
    group_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.update_group(group_id, server_group_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await server_groups_response(request, admin, service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#server-groups-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/servers/groups/{group_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_server_group_action(
    group_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.delete_group(group_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await server_groups_response(request, admin, service)


@router.get("/fragments/servers/routes/table", response_class=HTMLResponse, include_in_schema=False)
async def server_routes_table(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await server_routes_response(request, admin, service)


@router.get("/fragments/servers/routes/form", response_class=HTMLResponse, include_in_schema=False)
async def server_route_form(
    request: Request,
    route_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    route = await _find_by_id(await service.list_routes(), route_id)
    return template(
        "admin/fragments/server_route_form.html.j2",
        request,
        {"admin": admin, "route": route, "actions": ROUTE_ACTIONS},
    )


@router.post("/actions/servers/routes", response_class=HTMLResponse, include_in_schema=False)
async def create_server_route_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.create_route(server_route_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await server_routes_response(request, admin, service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#server-routes-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/servers/routes/{route_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_server_route_action(
    route_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.update_route(route_id, server_route_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await server_routes_response(request, admin, service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#server-routes-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/servers/routes/{route_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_server_route_action(
    route_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.delete_route(route_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await server_routes_response(request, admin, service)


@router.get("/fragments/servers/nodes/table", response_class=HTMLResponse, include_in_schema=False)
async def server_nodes_table(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    return await server_nodes_response(request, admin, service)


@router.get("/fragments/servers/nodes/form", response_class=HTMLResponse, include_in_schema=False)
async def server_node_form(
    request: Request,
    node_id: int | None = None,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    node = await service.get_node(node_id) if node_id else None
    return template(
        "admin/fragments/server_node_form.html.j2",
        request,
        {
            "admin": admin,
            "node": node,
            "groups": await service.list_groups(),
            "routes": await service.list_routes(),
            "protocols": PROTOCOLS,
            "networks": NETWORKS,
        },
    )


@router.post("/actions/servers/nodes", response_class=HTMLResponse, include_in_schema=False)
async def create_server_node_action(
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.create_node(server_node_create_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await server_nodes_response(request, admin, service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#server-nodes-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/servers/nodes/{node_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_server_node_action(
    node_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.update_node(node_id, server_node_update_from_form(form))
    except (ValidationError, ValueError) as exc:
        return action_error(request, validation_error_message(exc))
    except AppException as exc:
        return action_error(request, exc.detail)
    response = await server_nodes_response(request, admin, service)
    response.headers["HX-Trigger"] = "admin:close-modal"
    response.headers["HX-Retarget"] = "#server-nodes-table"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/actions/servers/nodes/{node_id}/copy", response_class=HTMLResponse, include_in_schema=False)
async def copy_server_node_action(
    node_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.copy_node(node_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await server_nodes_response(request, admin, service)


@router.post("/actions/servers/nodes/{node_id}/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_server_node_action(
    node_id: int,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    service: ServerAdminService = Depends(get_server_admin_service),
):
    admin = await current_admin(request, auth)
    if admin is None:
        return unauthorized_fragment()
    form = await form_data(request)
    if not valid_csrf(request, form):
        return action_error(request, "CSRF 校验失败")
    try:
        await service.delete_node(node_id)
    except AppException as exc:
        return action_error(request, exc.detail)
    return await server_nodes_response(request, admin, service)


async def server_groups_response(request: Request, admin: UserRead, service: ServerAdminService):
    return template(
        "admin/fragments/server_groups_table.html.j2",
        request,
        {"admin": admin, "groups": await service.list_groups()},
    )


async def server_routes_response(request: Request, admin: UserRead, service: ServerAdminService):
    return template(
        "admin/fragments/server_routes_table.html.j2",
        request,
        {"admin": admin, "routes": await service.list_routes()},
    )


async def server_nodes_response(request: Request, admin: UserRead, service: ServerAdminService):
    return template(
        "admin/fragments/server_nodes_table.html.j2",
        request,
        {"admin": admin, "nodes": await service.list_nodes()},
    )


async def _find_by_id(items: list[dict[str, Any]], item_id: int | None) -> dict[str, Any] | None:
    if item_id is None:
        return None
    return next((item for item in items if item.get("id") == item_id), None)
