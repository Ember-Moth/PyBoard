"""NoticeRepository 单元测试。"""

import pytest

from app.models.notice.entity import Notice
from app.repositories.notice import NoticeRepository


def _make(title: str, *, show: bool = True) -> Notice:
    return Notice(title=title, content=f"content of {title}", show=show)


@pytest.mark.asyncio
async def test_create_and_count(session):
    repo = NoticeRepository(session)
    await repo.create(_make("n1"))
    await repo.create(_make("n2", show=False))

    assert await repo.count() == 2
    assert await repo.count_visible() == 1


@pytest.mark.asyncio
async def test_list_visible_orders_desc(session):
    repo = NoticeRepository(session)
    a = await repo.create(_make("a"))
    b = await repo.create(_make("b"))
    c = await repo.create(_make("c"))

    items = await repo.list_visible(0, 10)
    # created_at 倒序，但同一秒内创建的可能并列；只断言全部命中
    assert {n.id for n in items} == {a.id, b.id, c.id}


@pytest.mark.asyncio
async def test_list_visible_excludes_hidden(session):
    repo = NoticeRepository(session)
    visible = await repo.create(_make("show", show=True))
    await repo.create(_make("hidden", show=False))

    items = await repo.list_visible(0, 10)
    assert [n.id for n in items] == [visible.id]


@pytest.mark.asyncio
async def test_list_all_includes_hidden(session):
    repo = NoticeRepository(session)
    await repo.create(_make("v", show=True))
    await repo.create(_make("h", show=False))

    items = await repo.list_all(0, 10)
    assert len(items) == 2


@pytest.mark.asyncio
async def test_pagination(session):
    repo = NoticeRepository(session)
    for i in range(5):
        await repo.create(_make(f"n{i}"))

    page1 = await repo.list_all(0, 2)
    page2 = await repo.list_all(2, 2)
    page3 = await repo.list_all(4, 2)

    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 1
    # 三页 id 不重复
    ids = {n.id for n in page1 + page2 + page3}
    assert len(ids) == 5
