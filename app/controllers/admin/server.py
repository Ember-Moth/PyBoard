"""管理端节点模块。"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin, get_server_admin_service
from app.core.response_utils import created, success
from app.models.server_group.dto import ServerGroupCreate, ServerGroupUpdate
from app.models.server_route.dto import ServerRouteCreate, ServerRouteUpdate
from app.models.server_v2node.dto import ServerV2NodeCreate, ServerV2NodeUpdate
from app.schemas.response import ApiResponse
from app.services.server_admin import ServerAdminService

router = APIRouter(
    prefix="/api/v1/admin/servers",
    tags=["管理-节点"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/groups", response_model=ApiResponse[list])
async def list_groups(service: ServerAdminService = Depends(get_server_admin_service)):
    return success(data=await service.list_groups())


@router.post("/groups", response_model=ApiResponse, status_code=201)
async def create_group(
    data: ServerGroupCreate,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return created(data=await service.create_group(data))


@router.patch("/groups/{group_id}", response_model=ApiResponse)
async def update_group(
    group_id: int,
    data: ServerGroupUpdate,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return success(data=await service.update_group(group_id, data))


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    await service.delete_group(group_id)


@router.get("/routes", response_model=ApiResponse[list])
async def list_routes(service: ServerAdminService = Depends(get_server_admin_service)):
    return success(data=await service.list_routes())


@router.post("/routes", response_model=ApiResponse, status_code=201)
async def create_route(
    data: ServerRouteCreate,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return created(data=await service.create_route(data))


@router.patch("/routes/{route_id}", response_model=ApiResponse)
async def update_route(
    route_id: int,
    data: ServerRouteUpdate,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return success(data=await service.update_route(route_id, data))


@router.delete("/routes/{route_id}", status_code=204)
async def delete_route(
    route_id: int,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    await service.delete_route(route_id)


@router.get("/nodes", response_model=ApiResponse[list])
async def list_nodes(service: ServerAdminService = Depends(get_server_admin_service)):
    return success(data=await service.list_nodes())


@router.get("/nodes/{node_id}", response_model=ApiResponse)
async def get_node(
    node_id: int,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return success(data=await service.get_node(node_id))


@router.post("/nodes", response_model=ApiResponse, status_code=201)
async def create_node(
    data: ServerV2NodeCreate,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return created(data=await service.create_node(data))


@router.patch("/nodes/{node_id}", response_model=ApiResponse)
async def update_node(
    node_id: int,
    data: ServerV2NodeUpdate,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return success(data=await service.update_node(node_id, data))


@router.delete("/nodes/{node_id}", status_code=204)
async def delete_node(
    node_id: int,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    await service.delete_node(node_id)


@router.post("/nodes/{node_id}/copy", response_model=ApiResponse)
async def copy_node(
    node_id: int,
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return success(data=await service.copy_node(node_id))


@router.post("/nodes/sort", response_model=ApiResponse[bool])
async def sort_nodes(
    data: dict[int | str, int],
    service: ServerAdminService = Depends(get_server_admin_service),
):
    return success(data=await service.sort_nodes(data))
