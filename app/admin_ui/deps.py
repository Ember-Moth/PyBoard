"""Admin HTML UI 公共依赖和工具。"""

import secrets
import urllib.parse
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.core.exceptions import AppException
from app.models.user.dto import UserRead
from app.services.auth import AuthService

TOKEN_COOKIE = "admin_token"
CSRF_COOKIE = "admin_csrf"
templates = Jinja2Templates(directory="app/templates")


async def current_admin(request: Request, auth: AuthService) -> UserRead | None:
    token = request.cookies.get(TOKEN_COOKIE)
    if not token:
        return None
    try:
        return await auth.require_admin(token)
    except AppException:
        return None


def page(template_name: str, request: Request, user: UserRead, active: str, title: str):
    csrf = request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(32)
    response = template(
        template_name,
        request,
        {"admin": user, "active": active, "title": title, "csrf_token": csrf},
    )
    set_csrf_cookie(response, csrf)
    return response


def template(template_name: str, request: Request, context: dict[str, Any]):
    return templates.TemplateResponse(request, template_name, context)


def login_error(request: Request, error: str, next_url: str):
    csrf = request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(32)
    response = template(
        "admin/login.html.j2",
        request,
        {"csrf_token": csrf, "next": next_url, "error": error},
    )
    set_csrf_cookie(response, csrf)
    return response


def redirect_to_login(request: Request):
    return RedirectResponse(f"/admin/login?next={urllib.parse.quote(str(request.url.path))}", status_code=303)


def set_csrf_cookie(response: Response, csrf: str) -> None:
    response.set_cookie(CSRF_COOKIE, csrf, httponly=True, samesite="lax", secure=False)


def valid_csrf(request: Request, form: dict[str, str]) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    submitted = request.headers.get("x-csrf-token") or form.get("csrf_token")
    return bool(cookie_token and submitted and secrets.compare_digest(cookie_token, submitted))


async def form_data(request: Request) -> dict[str, str]:
    body = (await request.body()).decode()
    parsed = urllib.parse.parse_qs(body, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def action_error(request: Request, message: str):
    return template("admin/fragments/action_error.html.j2", request, {"message": message})


def validation_error_message(exc: ValidationError | ValueError) -> str:
    if isinstance(exc, ValidationError):
        first_error = exc.errors()[0] if exc.errors() else {}
        return str(first_error.get("msg") or "表单参数不正确")
    return str(exc) or "表单参数不正确"


def unauthorized_fragment():
    return HTMLResponse(
        '<div class="alert alert-danger m-3">登录已失效，请重新登录。</div>',
        status_code=401,
        headers={"HX-Redirect": "/admin/login"},
    )


def filters_from_request(request: Request, form: dict[str, str] | None = None) -> dict[str, str]:
    source = form or dict(request.query_params)
    return {
        "q": str(source.get("q") or ""),
        "status": str(source.get("status") or ""),
        "offset": str(source.get("offset") or "0"),
        "limit": str(source.get("limit") or "20"),
    }


def blank_none(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def int_or_none(value: str | None) -> int | None:
    value = (value or "").strip()
    return int(value) if value else None


def float_or_none(value: str | None) -> float | None:
    value = (value or "").strip()
    return float(value) if value else None


def required_int(value: str | None) -> int:
    parsed = int_or_none(value)
    if parsed is None:
        raise ValueError("必填数字字段不能为空")
    return parsed


def as_bool(value: str | None) -> bool:
    return str(value or "").lower() in {"1", "true", "on", "yes"}
