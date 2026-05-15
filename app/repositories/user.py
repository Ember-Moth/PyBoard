"""User 仓储层 —— 用户数据访问。"""

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.order.entity import Order
from app.models.ticket.entity import Ticket
from app.models.user.entity import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户专用 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱查找用户。"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, user_id: int) -> User | None:
        """锁定用户行，用于余额、流量、套餐权益等强一致变更。"""
        stmt = select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否已注册。"""
        user = await self.get_by_email(email)
        return user is not None

    async def search_users(
        self,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        status: str | None = None,
    ) -> list[User]:
        """按邮箱/ID/状态搜索用户。"""
        stmt = select(User)
        if q:
            keyword = q.strip()
            if keyword.isdigit():
                stmt = stmt.where(or_(User.id == int(keyword), User.email.ilike(f"%{keyword}%")))  # type: ignore[attr-defined]
            else:
                stmt = stmt.where(User.email.ilike(f"%{keyword}%"))  # type: ignore[attr-defined]
        if status == "banned":
            stmt = stmt.where(User.banned.is_(True))  # type: ignore[attr-defined]
        elif status == "active":
            stmt = stmt.where(User.banned.is_(False))  # type: ignore[attr-defined]
        elif status == "admin":
            stmt = stmt.where(User.is_admin.is_(True))  # type: ignore[attr-defined]
        elif status == "staff":
            stmt = stmt.where(User.is_staff.is_(True))  # type: ignore[attr-defined]
        stmt = stmt.order_by(User.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_invited_users(self, user_id: int) -> int:
        """统计被该用户邀请注册的人数。"""
        stmt = select(func.count()).select_from(User).where(User.invite_user_id == user_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def count_pending_orders(self, user_id: int) -> int:
        """统计用户待支付订单数量。"""
        stmt = select(func.count()).select_from(Order).where(Order.user_id == user_id).where(Order.status == 0)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def count_open_tickets(self, user_id: int) -> int:
        """统计用户未关闭工单数量。"""
        stmt = select(func.count()).select_from(Ticket).where(Ticket.user_id == user_id).where(Ticket.status == 0)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def get_by_token(self, token: str) -> User | None:
        """根据订阅/安全 token 查询用户。"""
        stmt = select(User).where(User.token == token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """根据 Telegram ID 查询用户。"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
