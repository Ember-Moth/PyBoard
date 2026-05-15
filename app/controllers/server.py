"""V2Node 服务端 API。"""

import hashlib
from typing import Any

import msgpack
import orjson
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.core.deps import get_server_service
from app.core.queue import PostgresQueue, get_queue
from app.services.server import ServerService

router = APIRouter(prefix="/api/v2/server", tags=["V2Node 服务端"])
uniproxy_router = APIRouter(prefix="/api/v1/server", tags=["UniProxy 服务端"])


@router.api_route("/config", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def config(
    request: Request,
    service: ServerService = Depends(get_server_service),
):
    """1:1 复刻原版 V2\\Server\\ServerController@config。"""
    params = await _request_input(request)
    token = params.get("token")
    if not token:
        return _fail("token is null")

    expected_token = await service.setting_service.get_str("server_token", "")
    if str(token) != expected_token:
        return _fail("token is error")

    node_id = _to_int(params.get("node_id"))
    if node_id is None:
        return _fail("server is not exist")

    payload = await service.get_v2node_config(node_id)
    if payload is None:
        return _fail("server is not exist")

    body = orjson.dumps(payload)
    etag = hashlib.sha1(body).hexdigest()
    if _etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": f"\"{etag}\""})
    return Response(
        content=body,
        media_type="application/json",
        headers={"ETag": f"\"{etag}\""},
    )


async def _request_input(request: Request) -> dict[str, Any]:
    """Laravel Request::input 兼容：query + JSON/form body。"""
    data: dict[str, Any] = dict(request.query_params)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            data.update(body)
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        data.update(dict(form))
    return data


def _fail(message: str) -> JSONResponse:
    return JSONResponse(status_code=200, content={"status": "fail", "message": message})


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _etag_matches(header: str | None, etag: str) -> bool:
    if not header:
        return False
    return any(item.strip().strip('"') == etag for item in header.split(","))


@uniproxy_router.api_route("/{controller}/user", methods=["GET", "POST"])
async def uniproxy_user(
    controller: str,
    request: Request,
    service: ServerService = Depends(get_server_service),
):
    """复刻 UniProxyController@user。"""
    context = await _uniproxy_context(controller, request, service)
    if isinstance(context, Response):
        return context
    node_type, node_id, node = context
    await service.mark_uniproxy_check(node_type, int(node.id or node_id))
    payload = {"users": await service.get_available_users(node.group_id)}

    accept_format = request.headers.get("x-response-format", "")
    if "msgpack" in accept_format:
        body = msgpack.packb(payload, use_bin_type=True)
        etag = hashlib.sha1(body).hexdigest()
        if _etag_matches(request.headers.get("if-none-match"), etag):
            return Response(status_code=304, headers={"ETag": f"\"{etag}\""})
        return Response(
            content=body,
            media_type="application/x-msgpack",
            headers={"ETag": f"\"{etag}\""},
        )

    body = orjson.dumps(payload)
    etag = hashlib.sha1(body).hexdigest()
    if _etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": f"\"{etag}\""})
    return Response(content=body, media_type="application/json", headers={"ETag": f"\"{etag}\""})


@uniproxy_router.api_route("/{controller}/push", methods=["GET", "POST"])
async def uniproxy_push(
    controller: str,
    request: Request,
    service: ServerService = Depends(get_server_service),
    queue: PostgresQueue = Depends(get_queue),
):
    """复刻 UniProxyController@push。"""
    context = await _uniproxy_context(controller, request, service)
    if isinstance(context, Response):
        return context
    node_type, node_id, node = context
    data, invalid_json = await _request_data(request)
    if invalid_json:
        return JSONResponse(status_code=400, content={"error": "Invalid traffic data"})
    if not isinstance(data, dict):
        data = {}
    await service.handle_uniproxy_push(node, node_type, data, queue)
    return {"data": True}


@uniproxy_router.api_route("/{controller}/alivelist", methods=["GET", "POST"])
async def uniproxy_alivelist(
    controller: str,
    request: Request,
    service: ServerService = Depends(get_server_service),
):
    """复刻 UniProxyController@alivelist。"""
    context = await _uniproxy_context(controller, request, service)
    if isinstance(context, Response):
        return context
    return {"alive": await service.get_alive_list()}


@uniproxy_router.api_route("/{controller}/alive", methods=["GET", "POST"])
async def uniproxy_alive(
    controller: str,
    request: Request,
    service: ServerService = Depends(get_server_service),
):
    """复刻 UniProxyController@alive。"""
    context = await _uniproxy_context(controller, request, service)
    if isinstance(context, Response):
        return context
    node_type, node_id, _node = context
    data, _invalid_json = await _request_data(request)
    if not isinstance(data, dict):
        return JSONResponse(status_code=400, content={"error": "Invalid online data format"})
    await service.handle_alive(node_type, node_id, data)
    return {"data": True}


async def _uniproxy_context(
    controller: str,
    request: Request,
    service: ServerService,
) -> tuple[str, int, Any] | JSONResponse:
    if controller.lower() != "uniproxy":
        return JSONResponse(status_code=404, content={"message": "server controller is not exist"})

    params = await _request_input(request)
    token = params.get("token")
    if not token:
        return _abort("token is null")

    expected_token = await service.setting_service.get_str("server_token", "")
    if str(token) != expected_token:
        return _abort("token is error")

    node_type = _normalize_uniproxy_node_type(params.get("node_type"))
    node_id = _to_int(params.get("node_id"))
    if node_id is None:
        return _abort("server is not exist")

    node = await service.get_uniproxy_node(node_id, node_type)
    if node is None:
        return _abort("server is not exist")
    return node_type, node_id, node


async def _request_data(request: Request) -> tuple[Any, bool]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            return None, True
        return data, False
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return dict(form), False
    return {}, False


def _abort(message: str) -> JSONResponse:
    return JSONResponse(status_code=500, content={"message": message})


def _normalize_uniproxy_node_type(value: Any) -> str:
    node_type = str(value or "")
    if node_type == "v2ray":
        return "vmess"
    if node_type == "hysteria2":
        return "hysteria"
    return node_type
