"""V2Node 节点 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.server_v2node.entity import ServerV2Node
from app.repositories.base import BaseRepository


class ServerV2NodeRepository(BaseRepository[ServerV2Node]):
    """V2Node 节点专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, ServerV2Node)

    async def list_all(self) -> list[ServerV2Node]:
        stmt = select(ServerV2Node).order_by(
            ServerV2Node.sort.asc().nulls_last(),  # type: ignore[union-attr]
            ServerV2Node.id.asc(),  # type: ignore[union-attr]
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_visible_by_group(self, group_id: int | None) -> list[ServerV2Node]:
        """查询用户分组可见节点。"""
        if group_id is None:
            return []
        stmt = (
            select(ServerV2Node)
            .where(ServerV2Node.show.is_(True))  # type: ignore[attr-defined]
            .order_by(
                ServerV2Node.sort.asc().nulls_last(),  # type: ignore[union-attr]
                ServerV2Node.id.asc(),  # type: ignore[union-attr]
            )
        )
        result = await self.db.execute(stmt)
        nodes = list(result.scalars().all())
        return [node for node in nodes if _group_contains(node.group_id, group_id)]


def _group_contains(raw_group_id, group_id: int) -> bool:
    if isinstance(raw_group_id, int):
        return raw_group_id == group_id
    if isinstance(raw_group_id, list):
        return str(group_id) in {str(item) for item in raw_group_id}
    value = str(raw_group_id or "")
    if value == str(group_id):
        return True
    try:
        import orjson

        parsed = orjson.loads(value)
    except Exception:
        parsed = [item.strip() for item in value.split(",")]
    if isinstance(parsed, int):
        return parsed == group_id
    if isinstance(parsed, list):
        return str(group_id) in {str(item) for item in parsed}
    return False
