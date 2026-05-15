"""通用响应体 —— code 与 HTTP 状态码一致。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式，code 使用 HTTP 状态码。

    Examples:
        {"code": 200, "msg": "success", "data": {...}}
        {"code": 404, "msg": "用户不存在", "data": null}
    """

    code: int = 200
    msg: str = "success"
    data: T | None = None


class PaginatedData(BaseModel, Generic[T]):
    """分页数据载体，作为 ApiResponse.data 使用。

    Examples:
        ApiResponse[PaginatedData[NoticePublic]]
        → {"code": 200, "msg": "success",
            "data": {"items": [...], "total": 42, "page": 1, "size": 10}}
    """

    items: list[T]
    total: int
    page: int
    size: int
