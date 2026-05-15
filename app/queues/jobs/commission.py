"""佣金相关任务。"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_engine
from app.repositories.commission_log import CommissionLogRepository
from app.repositories.order import OrderRepository
from app.repositories.setting import SettingRepository
from app.repositories.user import UserRepository
from app.services.commission import CommissionService
from app.services.setting import SettingService


async def calc_commission(ctx: dict, order_id: int) -> None:
    """计算订单佣金。

    Args:
        order_id: 订单 ID
    """
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        order_repo = OrderRepository(db)
        order = await order_repo.get_by_id(order_id)
        if order is None:
            return
        service = CommissionService(
            CommissionLogRepository(db),
            order_repo,
            UserRepository(db),
            SettingService(SettingRepository(db)),
        )
        await service.calculate_for_order(order)
        await db.commit()
