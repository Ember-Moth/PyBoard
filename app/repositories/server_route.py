"""服务器路由规则 Repository。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.server_route.entity import ServerRoute
from app.repositories.base import BaseRepository


class ServerRouteRepository(BaseRepository[ServerRoute]):
    """服务器路由规则专用查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, ServerRoute)

    async def list_all(self) -> list[ServerRoute]:
        stmt = select(ServerRoute).order_by(ServerRoute.id.asc())  # type: ignore[union-attr]
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids_ordered(self, route_ids: list[int]) -> list[ServerRoute]:
        """按传入 ID 顺序返回路由规则。"""
        if not route_ids:
            return []
        stmt = select(ServerRoute).where(ServerRoute.id.in_(route_ids))  # type: ignore[attr-defined]
        result = await self.db.execute(stmt)
        routes = {route.id: route for route in result.scalars().all()}
        return [routes[route_id] for route_id in route_ids if route_id in routes]
