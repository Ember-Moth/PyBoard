"""HTTP 请求日志中间件。"""

import logging
import time
import traceback
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, Request, Response
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import QueryParams

from app.admin_ui.deps import TOKEN_COOKIE
from app.core.config import settings
from app.core.database import get_db
from app.services.log_event import create_log_event

logger = logging.getLogger(__name__)

_SENSITIVE_KEYS = {
    "authorization",
    "csrf",
    "csrf_token",
    "email_code",
    "key",
    "password",
    "secret",
    "sign",
    "token",
}


async def request_logging_middleware(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """记录 API、回调和 Admin UI 请求，不记录 body。"""
    if not _should_log(request.url.path):
        return await call_next(request)

    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    trace_id = request.headers.get("X-Trace-ID")
    request.state.request_id = request_id
    start = time.perf_counter()
    response: Response | None = None
    error: Exception | None = None
    error_stack: str | None = None

    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        error = exc
        error_stack = traceback.format_exc()
        raise
    finally:
        status_code = response.status_code if response is not None else 500
        duration_ms = max(int((time.perf_counter() - start) * 1000), 0)
        if response is not None:
            response.headers["X-Request-ID"] = request_id
        await _safe_write_access_event(
            request,
            request_id=request_id,
            trace_id=trace_id,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error,
            error_stack=error_stack,
        )


def register_request_logging(app: FastAPI) -> None:
    """注册 HTTP 请求日志中间件。"""
    app.middleware("http")(request_logging_middleware)


async def _safe_write_access_event(
    request: Request,
    *,
    request_id: str,
    trace_id: str | None,
    status_code: int,
    duration_ms: int,
    error: Exception | None,
    error_stack: str | None,
) -> None:
    try:
        async with _logging_db(request.app) as db:
            actor_type, actor_id = _actor_from_request(request)
            await create_log_event(
                db,
                level=_level_for(status_code, error),
                category="access",
                event="http.request",
                message=f"{request.method} {request.url.path} -> {status_code}",
                request_id=request_id,
                trace_id=trace_id,
                actor_type=actor_type,
                actor_id=actor_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
                ip=_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                data={
                    "query": _redact_query(request.query_params),
                    "route": getattr(request.scope.get("route"), "path", None),
                },
                error_type=type(error).__name__ if error else None,
                error_stack=error_stack,
            )
    except Exception:
        logger.exception("failed to write request log event")


@asynccontextmanager
async def _logging_db(app: FastAPI) -> AsyncIterator[AsyncSession]:
    provider = app.dependency_overrides.get(get_db, get_db)
    resource = provider()
    if hasattr(resource, "__anext__"):
        agen = resource  # type: ignore[assignment]
        db = await anext(agen)
        try:
            yield db
        except Exception as exc:
            with suppress(Exception):
                await agen.athrow(type(exc), exc, exc.__traceback__)
            raise
        else:
            with suppress(StopAsyncIteration):
                await anext(agen)
        finally:
            with suppress(Exception):
                await agen.aclose()
        return
    yield resource


def _should_log(path: str) -> bool:
    if path.startswith("/admin/fragments/logs"):
        return False
    return path.startswith(("/api/", "/notify/", "/admin/"))


def _level_for(status_code: int, error: Exception | None) -> str:
    if error is not None or status_code >= 500:
        return "error"
    if status_code >= 400:
        return "warning"
    return "info"


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or None
    return request.client.host if request.client else None


def _redact_query(params: QueryParams) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in params.multi_items():
        stored = "***" if _is_sensitive_key(key) else value
        if key in redacted:
            existing = redacted[key]
            if isinstance(existing, list):
                existing.append(stored)
            else:
                redacted[key] = [existing, stored]
        else:
            redacted[key] = stored
    return redacted


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return lowered in _SENSITIVE_KEYS or any(part in lowered for part in ("token", "password", "secret"))


def _actor_from_request(request: Request) -> tuple[str | None, int | None]:
    token = _bearer_token(request.headers.get("authorization")) or request.cookies.get(TOKEN_COOKIE)
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        return ("user", int(subject)) if subject is not None else (None, None)
    except (JWTError, TypeError, ValueError):
        return None, None


def _bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token else None
