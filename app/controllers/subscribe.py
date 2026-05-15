"""订阅控制器。"""

import hashlib

import orjson
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user, get_subscribe_service
from app.core.response_utils import success
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.subscribe import SubscribeService

client_router = APIRouter(prefix="/api/v1/client", tags=["订阅"])
user_router = APIRouter(prefix="/api/v1/user", tags=["用户订阅"])


@client_router.get("/subscribe")
async def subscribe(
    request: Request,
    token: str = Query(""),
    flag: str | None = Query(None),
    service: SubscribeService = Depends(get_subscribe_service),
):
    """客户端订阅入口。"""
    user = await service.resolve_subscribe_user(token)
    content, media_type, headers = await service.render_subscription(
        user,
        flag or request.headers.get("User-Agent", ""),
    )
    return Response(content=content, media_type=media_type, headers=headers)


@user_router.get("/subscribe", response_model=ApiResponse[dict])
async def get_subscribe_info(
    current_user: UserRead = Depends(get_current_user),
    service: SubscribeService = Depends(get_subscribe_service),
):
    """获取当前用户订阅信息。"""
    return success(data=await service.get_user_subscribe_info(current_user.id))


@user_router.get("/servers", response_model=ApiResponse[list])
async def get_user_servers(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: SubscribeService = Depends(get_subscribe_service),
):
    """获取当前用户可用节点列表。"""
    user = await service.user_repo.get_by_id(current_user.id)
    servers = await service.get_available_servers(user) if user else []
    etag = hashlib.sha1(orjson.dumps([server.get("cache_key") for server in servers])).hexdigest()
    if request.headers.get("If-None-Match", "").strip('"') == etag:
        return Response(status_code=304, headers={"ETag": f'"{etag}"'})
    return JSONResponse(content=success(data=servers), headers={"ETag": f'"{etag}"'})
