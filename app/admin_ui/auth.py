"""Admin 登录和入口路由。"""

import secrets

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.admin_ui.deps import (
    CSRF_COOKIE,
    TOKEN_COOKIE,
    current_admin,
    form_data,
    login_error,
    set_csrf_cookie,
    template,
)
from app.core.deps import get_auth_service
from app.core.exceptions import AppException
from app.models.user.dto import LoginRequest
from app.services.auth import AuthService

router = APIRouter()


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request, auth: AuthService = Depends(get_auth_service)):
    user = await current_admin(request, auth)
    if user is not None:
        return RedirectResponse("/admin/dashboard", status_code=303)
    csrf = request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(32)
    response = template(
        "admin/login.html.j2",
        request,
        {"csrf_token": csrf, "next": request.query_params.get("next") or "/admin/dashboard", "error": ""},
    )
    set_csrf_cookie(response, csrf)
    return response


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_submit(request: Request, auth: AuthService = Depends(get_auth_service)):
    form = await form_data(request)
    csrf = request.cookies.get(CSRF_COOKIE)
    if not csrf or csrf != form.get("csrf_token"):
        return login_error(request, "页面已过期，请刷新后重试", form.get("next") or "/admin/dashboard")
    try:
        token = await auth.login(
            LoginRequest(email=str(form.get("email") or ""), password=str(form.get("password") or "")),
            verify_turnstile=False,
        )
        raw_token = token.auth_token.removeprefix("Bearer ").strip()
        await auth.require_admin(raw_token)
    except AppException as exc:
        return login_error(request, exc.detail, form.get("next") or "/admin/dashboard")

    csrf = secrets.token_urlsafe(32)
    response = RedirectResponse(str(form.get("next") or "/admin/dashboard"), status_code=303)
    response.set_cookie(TOKEN_COOKIE, raw_token, httponly=True, samesite="lax", secure=False)
    set_csrf_cookie(response, csrf)
    return response


@router.get("/logout", include_in_schema=False)
async def logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(TOKEN_COOKIE)
    response.delete_cookie(CSRF_COOKIE)
    return response
