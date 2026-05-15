"""Knowledge 服务层 —— 知识库业务逻辑。"""

import base64
import re
import urllib.parse
from typing import Any

from jinja2 import Environment

from app.core.exceptions import NotFoundException
from app.models.knowledge.dto import (
    KnowledgeCreate,
    KnowledgePublic,
    KnowledgeRead,
    KnowledgeUpdate,
)
from app.models.knowledge.entity import Knowledge
from app.repositories.knowledge import KnowledgeRepository
from app.schemas.response import PaginatedData


class KnowledgeService:
    """知识库业务逻辑。"""

    def __init__(self, repo: KnowledgeRepository):
        self.repo = repo

    # ---- 用户端 ----
    async def list_grouped_by_category(
        self,
        *,
        language: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, list[KnowledgePublic]]:
        """按分类分组返回已上线知识列表。"""
        items = await self.repo.list_visible(language=language, keyword=keyword)
        grouped: dict[str, list[KnowledgePublic]] = {}
        for item in items:
            grouped.setdefault(item.category, []).append(_to_public(item))
        return grouped

    async def get_public(self, knowledge_id: int, render_context: dict[str, Any] | None = None) -> KnowledgeRead:
        """用户端详情 —— 仅返回已上线，且对 body 做后处理。"""
        knowledge = await self.repo.get_visible(knowledge_id)
        if knowledge is None:
            raise NotFoundException(f"知识 {knowledge_id} 不存在")
        result = _to_read(knowledge)
        result.body = _render_body(result.body, render_context)
        return result

    async def list_languages(self) -> list[str]:
        """已上线知识涉及的语言列表。"""
        return sorted(await self.repo.list_languages())

    # ---- 管理端 ----
    async def list_all(self, page: int, size: int) -> PaginatedData[KnowledgeRead]:
        offset = (page - 1) * size
        items = await self.repo.list_all(offset, size)
        total = await self.repo.count()
        return PaginatedData(
            items=[_to_read(k) for k in items],
            total=total,
            page=page,
            size=size,
        )

    async def get(self, knowledge_id: int) -> KnowledgeRead:
        knowledge = await self.repo.get_by_id(knowledge_id)
        if knowledge is None:
            raise NotFoundException(f"知识 {knowledge_id} 不存在")
        return _to_read(knowledge)

    async def create(self, data: KnowledgeCreate) -> KnowledgeRead:
        knowledge = Knowledge(**data.model_dump())
        knowledge = await self.repo.create(knowledge)
        return _to_read(knowledge)

    async def update(self, knowledge_id: int, data: KnowledgeUpdate) -> KnowledgeRead:
        knowledge = await self.repo.get_by_id(knowledge_id)
        if knowledge is None:
            raise NotFoundException(f"知识 {knowledge_id} 不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(knowledge, field, value)
        knowledge = await self.repo.update(knowledge)
        return _to_read(knowledge)

    async def delete(self, knowledge_id: int) -> None:
        knowledge = await self.repo.get_by_id(knowledge_id)
        if knowledge is None:
            raise NotFoundException(f"知识 {knowledge_id} 不存在")
        await self.repo.delete(knowledge)


def _to_public(k: Knowledge) -> KnowledgePublic:
    return KnowledgePublic.model_validate(k, from_attributes=True)


def _to_read(k: Knowledge) -> KnowledgeRead:
    return KnowledgeRead.model_validate(k, from_attributes=True)


def _render_body(body: str, context: dict[str, Any] | None = None) -> str:
    """使用 Jinja2 渲染知识库正文，并处理订阅用户可见内容。"""
    context = context or {}
    has_subscribe = bool(context.get("subscribeUrl"))
    if not has_subscribe:
        body = re.sub(r"<!--access start-->.*?<!--access end-->", "", body, flags=re.S)
    return Environment(autoescape=False).from_string(body).render(**_knowledge_context(context))


def _knowledge_context(context: dict[str, Any]) -> dict[str, Any]:
    subscribe_url = str(context.get("subscribeUrl") or "")
    subscribe_token = str(context.get("subscribeToken") or "")
    return {
        **context,
        "siteName": context.get("siteName") or "",
        "subscribeUrl": subscribe_url,
        "urlEncodeSubscribeUrl": urllib.parse.quote(subscribe_url),
        "safeBase64SubscribeUrl": base64.urlsafe_b64encode(subscribe_url.encode()).decode().rstrip("="),
        "subscribeToken": subscribe_token,
    }
