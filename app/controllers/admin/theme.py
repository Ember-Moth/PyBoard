"""主题 管理端控制器。"""

from typing import Any

from fastapi import APIRouter, Body, Depends

from app.core.deps import get_current_admin, get_theme_service
from app.core.response_utils import success
from app.schemas.response import ApiResponse
from app.services.theme import ThemeService

router = APIRouter(
    prefix="/api/v1/admin/themes",
    tags=["管理-主题"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[dict])
async def list_themes(service: ThemeService = Depends(get_theme_service)):
    """获取主题列表。"""
    return success(data=await service.list_themes())


@router.get("/{name}/config", response_model=ApiResponse[dict])
async def get_theme_config(name: str, service: ThemeService = Depends(get_theme_service)):
    """获取主题配置。"""
    return success(data=await service.get_theme_config(name))


@router.put("/{name}/config", response_model=ApiResponse[dict])
async def save_theme_config(
    name: str,
    config: str | dict[str, Any] = Body(..., embed=True),
    service: ThemeService = Depends(get_theme_service),
):
    """保存主题配置。"""
    return success(data=await service.save_theme_config(name, config))
