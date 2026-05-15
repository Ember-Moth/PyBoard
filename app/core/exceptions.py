"""统一异常类 —— 语义化 HTTP 错误。"""


class AppException(Exception):
    """应用异常基类。"""

    status_code: int = 500
    detail: str = "内部错误"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundException(AppException):
    """资源不存在 → 404。"""

    status_code = 404
    detail = "资源不存在"


class ConflictException(AppException):
    """资源冲突 → 409。"""

    status_code = 409
    detail = "资源冲突"


class BadRequestException(AppException):
    """请求参数错误 → 400。"""

    status_code = 400
    detail = "请求参数错误"


class UnauthorizedException(AppException):
    """未认证 → 401。"""

    status_code = 401
    detail = "未登录或登录已过期"


class ForbiddenException(AppException):
    """无权限 → 403。"""

    status_code = 403
    detail = "无权限访问"
