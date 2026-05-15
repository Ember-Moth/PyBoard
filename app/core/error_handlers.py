"""FastAPI 异常处理器 —— 将 AppException 转换为统一 ApiResponse 格式。"""

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.schemas.response import ApiResponse


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
    """所有 AppException 子类自动转为 {code, msg, data} 格式。"""
    if isinstance(exc, AppException):
        body = ApiResponse(code=exc.status_code, msg=exc.detail, data=None).model_dump()
        return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(body))
    body = ApiResponse(code=500, msg="Internal Server Error", data=None).model_dump()
    return JSONResponse(status_code=500, content=jsonable_encoder(body))


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """FastAPI/Starlette HTTPException 统一响应。"""
    msg = str(exc.detail) if exc.detail else "请求失败"
    body = ApiResponse(code=exc.status_code, msg=msg, data=None).model_dump()
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(body))


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """请求参数校验错误统一响应。"""
    prefix = "Value error, "
    errors = exc.errors()
    for err in errors:
        raw = str(err.get("msg", ""))
        err["msg"] = raw.removeprefix(prefix)
    msg = errors[0]["msg"] if errors else "请求参数错误"
    body = ApiResponse(code=422, msg=msg, data=errors).model_dump()
    return JSONResponse(status_code=422, content=jsonable_encoder(body))
