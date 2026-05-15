"""响应工具函数 —— 简化 ApiResponse 构造。"""

from app.schemas.response import ApiResponse


def success(*, data=None, msg: str = "success") -> dict:
    """构造成功响应（code=200）。

    Usage:
        return success(data=user)
        return success(data=users, msg="查询成功")
    """
    return ApiResponse(code=200, msg=msg, data=data).model_dump()


def created(*, data=None, msg: str = "success") -> dict:
    """构造创建成功响应（code=201）。"""
    return ApiResponse(code=201, msg=msg, data=data).model_dump()
