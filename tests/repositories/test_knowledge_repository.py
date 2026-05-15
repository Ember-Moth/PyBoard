"""KnowledgeRepository 单元测试。"""

import pytest

from app.models.knowledge.entity import Knowledge
from app.repositories.knowledge import KnowledgeRepository


def _make(
    title: str,
    *,
    language: str = "zh-CN",
    category: str = "general",
    body: str = "default body",
    sort: int | None = None,
    show: bool = True,
) -> Knowledge:
    return Knowledge(
        language=language,
        category=category,
        title=title,
        body=body,
        sort=sort,
        show=show,
    )


@pytest.mark.asyncio
async def test_list_visible_excludes_hidden(session):
    repo = KnowledgeRepository(session)
    visible = await repo.create(_make("v"))
    await repo.create(_make("h", show=False))

    items = await repo.list_visible()
    assert [k.id for k in items] == [visible.id]


@pytest.mark.asyncio
async def test_list_visible_filter_by_language(session):
    repo = KnowledgeRepository(session)
    cn = await repo.create(_make("cn", language="zh-CN"))
    await repo.create(_make("en", language="en-US"))

    items = await repo.list_visible(language="zh-CN")
    assert [k.id for k in items] == [cn.id]


@pytest.mark.asyncio
async def test_list_visible_keyword_searches_title_and_body(session):
    repo = KnowledgeRepository(session)
    in_title = await repo.create(_make("hello world", body="x"))
    in_body = await repo.create(_make("other", body="contains hello inside"))
    await repo.create(_make("nope", body="nothing relevant"))

    items = await repo.list_visible(keyword="hello")
    ids = {k.id for k in items}
    assert ids == {in_title.id, in_body.id}


@pytest.mark.asyncio
async def test_list_visible_orders_by_sort_then_id(session):
    repo = KnowledgeRepository(session)
    a = await repo.create(_make("a", sort=2))
    b = await repo.create(_make("b", sort=1))
    c = await repo.create(_make("c", sort=None))  # nulls last

    items = await repo.list_visible()
    assert [k.id for k in items] == [b.id, a.id, c.id]


@pytest.mark.asyncio
async def test_get_visible_returns_none_for_hidden(session):
    repo = KnowledgeRepository(session)
    hidden = await repo.create(_make("h", show=False))

    assert await repo.get_visible(hidden.id) is None  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_list_languages_distinct(session):
    repo = KnowledgeRepository(session)
    await repo.create(_make("a", language="zh-CN"))
    await repo.create(_make("b", language="zh-CN"))
    await repo.create(_make("c", language="en-US"))
    await repo.create(_make("d", language="ja-JP", show=False))  # 隐藏的不计

    langs = await repo.list_languages()
    assert sorted(langs) == ["en-US", "zh-CN"]
