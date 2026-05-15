"""Knowledge 用户端控制器 —— 知识库查询。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_knowledge_service, get_optional_current_user, get_setting_service, get_subscribe_service
from app.core.response_utils import success
from app.models.knowledge.dto import KnowledgePublic, KnowledgeRead
from app.schemas.response import ApiResponse
from app.services.knowledge import KnowledgeService
from app.services.setting import SettingService
from app.services.subscribe import SubscribeService

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库"])


@router.get("", response_model=ApiResponse[dict[str, list[KnowledgePublic]]])
async def list_knowledges(
    language: str | None = Query(None, max_length=5, description="语言过滤"),
    keyword: str | None = Query(None, max_length=64, description="标题/正文关键词"),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """已上线知识列表，按 category 分组。"""
    data = await service.list_grouped_by_category(language=language, keyword=keyword)
    return success(data=data)


@router.get("/languages", response_model=ApiResponse[list[str]])
async def list_languages(
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """已上线知识涉及的语言列表。"""
    data = await service.list_languages()
    return success(data=data)


@router.get("/{knowledge_id}", response_model=ApiResponse[KnowledgeRead])
async def get_knowledge(
    knowledge_id: int,
    current_user=Depends(get_optional_current_user),
    service: KnowledgeService = Depends(get_knowledge_service),
    setting_service: SettingService = Depends(get_setting_service),
    subscribe_service: SubscribeService = Depends(get_subscribe_service),
):
    """知识详情（仅返回已上线条目）。"""
    context = {"siteName": await setting_service.get_str("app_name", "PyBoard")}
    if current_user is not None:
        user = await subscribe_service.user_repo.get_by_id(current_user.id)
        if user is not None:
            context["subscribeUrl"] = await subscribe_service.build_subscribe_url(user)
            context["subscribeToken"] = user.token
    knowledge = await service.get_public(knowledge_id, context)
    return success(data=knowledge)
