"""订单处理队列任务，对齐原版 OrderHandleJob。"""

import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_engine
from app.repositories.order import OrderRepository
from app.repositories.setting import SettingRepository
from app.services.order import OrderService
from app.services.setting import SettingService


async def order_handle(ctx: dict, trade_no: str) -> None:
    """处理订单状态。

    原版逻辑：
    - status=0 且创建超过 2 小时：取消
    - status=1：开通订单
    """
    engine = get_engine()
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]
    async with session_factory() as db:  # type: ignore[operator]
        try:
            order_repo = OrderRepository(db)
            order = await order_repo.get_by_trade_no(trade_no)
            if order is None:
                return

            if order.status == 0:
                if order.created_at <= int(time.time()) - 3600 * 2:
                    order.status = 2
                    await order_repo.update(order)
            elif order.status == 1:
                service = OrderService(db, SettingService(SettingRepository(db)))
                await service._process_paid_order(order)

            await db.commit()
        except Exception:
            await db.rollback()
            raise
