"""Knowledge 管理端控制器 —— 知识库 CRUD。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_knowledge_service
from app.core.response_utils import created, success
from app.models.knowledge.dto import KnowledgeCreate, KnowledgeRead, KnowledgeUpdate
from app.schemas.response import ApiResponse, PaginatedData
from app.services.knowledge import KnowledgeService

router = APIRouter(
    prefix="/api/v1/admin/knowledge",
    tags=["管理-知识库"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[PaginatedData[KnowledgeRead]])
async def list_knowledges(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """全量知识列表（含未上线）。"""
    data = await service.list_all(page, size)
    return success(data=data)


@router.get("/{knowledge_id}", response_model=ApiResponse[KnowledgeRead])
async def get_knowledge(
    knowledge_id: int,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    knowledge = await service.get(knowledge_id)
    return success(data=knowledge)


@router.post("", response_model=ApiResponse[KnowledgeRead], status_code=201)
async def create_knowledge(
    data: KnowledgeCreate,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    knowledge = await service.create(data)
    return created(data=knowledge)


@router.patch("/{knowledge_id}", response_model=ApiResponse[KnowledgeRead])
async def update_knowledge(
    knowledge_id: int,
    data: KnowledgeUpdate,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    knowledge = await service.update(knowledge_id, data)
    return success(data=knowledge)


@router.delete("/{knowledge_id}", status_code=204)
async def delete_knowledge(
    knowledge_id: int,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    await service.delete(knowledge_id)
