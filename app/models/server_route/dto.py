"""ServerRoute DTO，接口视图，不做持久化。"""

from typing import Any

from sqlmodel import SQLModel


class ServerRouteCreate(SQLModel):
    remarks: str
    match: list[str] | str | None = None
    action: str
    action_value: str | dict[str, Any] | list[Any] | None = None


class ServerRouteUpdate(SQLModel):
    remarks: str | None = None
    match: list[str] | str | None = None
    action: str | None = None
    action_value: str | dict[str, Any] | list[Any] | None = None


class ServerRoutePublic(SQLModel):
    """服务器路由规则列表公开视图。"""

    id: int
    created_at: int


class ServerRouteRead(SQLModel):
    """服务器路由规则详情视图。"""

    id: int
    remarks: str
    match: list[str] | str
    action: str
    action_value: str | dict[str, Any] | list[Any] | None
    created_at: int
    updated_at: int
