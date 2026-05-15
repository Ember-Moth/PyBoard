"""Plan 服务层 —— 套餐业务逻辑。"""

from app.core.exceptions import ConflictException, NotFoundException
from app.models.plan.dto import (
    PlanAdminRead,
    PlanCreate,
    PlanPublic,
    PlanRead,
    PlanUpdate,
)
from app.models.plan.entity import Plan
from app.repositories.plan import PlanRepository


def _capacity_remaining(
    capacity_limit: int | None,
    active_count: int,
) -> int | None:
    """计算套餐剩余容量。None 表示不限制。"""
    if capacity_limit is None or capacity_limit <= 0:
        return None
    return max(0, capacity_limit - active_count)


class PlanService:
    """套餐业务逻辑。"""

    def __init__(self, repo: PlanRepository):
        self.repo = repo

    # ---- 用户端 ----
    async def list_visible(self) -> list[PlanPublic]:
        """已上线套餐列表，动态计算剩余容量。"""
        plans = await self.repo.list_visible()
        counts = await self.repo.count_active_users()
        return [
            PlanPublic(
                id=p.id,  # type: ignore[arg-type]
                group_id=p.group_id,
                transfer_enable=p.transfer_enable,
                device_limit=p.device_limit,
                name=p.name,
                speed_limit=p.speed_limit,
                sort=p.sort,
                content=p.content,
                month_price=p.month_price,
                quarter_price=p.quarter_price,
                half_year_price=p.half_year_price,
                year_price=p.year_price,
                two_year_price=p.two_year_price,
                three_year_price=p.three_year_price,
                onetime_price=p.onetime_price,
                reset_price=p.reset_price,
                reset_traffic_method=p.reset_traffic_method,
                capacity_limit=_capacity_remaining(p.capacity_limit, counts.get(p.id, 0)),  # type: ignore[arg-type]
                created_at=p.created_at,
            )
            for p in plans
        ]

    async def get_for_user(self, plan_id: int, current_user_plan_id: int | None) -> PlanRead:
        """用户端详情。

        规则：
        - show=True → 所有人可见
        - show=False 但 renew=True → 仅当前持有该套餐的用户可见（用于续费）
        """
        plan = await self.repo.get_by_id(plan_id)
        if plan is None:
            raise NotFoundException(f"套餐 {plan_id} 不存在")

        if not plan.show:
            # 隐藏套餐：要么可续费且用户当前持有才允许查看
            if not plan.renew or current_user_plan_id != plan.id:
                raise NotFoundException(f"套餐 {plan_id} 不存在")

        counts = await self.repo.count_active_users()
        return PlanRead(
            id=plan.id,  # type: ignore[arg-type]
            group_id=plan.group_id,
            transfer_enable=plan.transfer_enable,
            device_limit=plan.device_limit,
            name=plan.name,
            speed_limit=plan.speed_limit,
            sort=plan.sort,
            renew=plan.renew,
            content=plan.content,
            month_price=plan.month_price,
            quarter_price=plan.quarter_price,
            half_year_price=plan.half_year_price,
            year_price=plan.year_price,
            two_year_price=plan.two_year_price,
            three_year_price=plan.three_year_price,
            onetime_price=plan.onetime_price,
            reset_price=plan.reset_price,
            reset_traffic_method=plan.reset_traffic_method,
            capacity_limit=_capacity_remaining(plan.capacity_limit, counts.get(plan.id, 0)),  # type: ignore[arg-type]
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    async def has_capacity(self, plan_id: int) -> bool:
        """容量校验 —— 检查套餐是否还有余量（Order 模块调用）。"""
        plan = await self.repo.get_by_id(plan_id)
        if plan is None:
            raise NotFoundException(f"套餐 {plan_id} 不存在")
        if plan.capacity_limit is None or plan.capacity_limit <= 0:
            return True
        counts = await self.repo.count_active_users()
        return counts.get(plan_id, 0) < plan.capacity_limit

    # ---- 管理端 ----
    async def list_all(self) -> list[PlanAdminRead]:
        """管理端全量列表，附带活跃用户计数。"""
        plans = await self.repo.list_all()
        counts = await self.repo.count_active_users()
        return [
            PlanAdminRead(
                id=p.id,  # type: ignore[arg-type]
                group_id=p.group_id,
                transfer_enable=p.transfer_enable,
                device_limit=p.device_limit,
                name=p.name,
                speed_limit=p.speed_limit,
                show=p.show,
                sort=p.sort,
                renew=p.renew,
                content=p.content,
                month_price=p.month_price,
                quarter_price=p.quarter_price,
                half_year_price=p.half_year_price,
                year_price=p.year_price,
                two_year_price=p.two_year_price,
                three_year_price=p.three_year_price,
                onetime_price=p.onetime_price,
                reset_price=p.reset_price,
                reset_traffic_method=p.reset_traffic_method,
                capacity_limit=p.capacity_limit,
                count=counts.get(p.id, 0),  # type: ignore[arg-type]
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in plans
        ]

    async def get(self, plan_id: int) -> PlanAdminRead:
        """管理端详情。"""
        plan = await self.repo.get_by_id(plan_id)
        if plan is None:
            raise NotFoundException(f"套餐 {plan_id} 不存在")
        counts = await self.repo.count_active_users()
        return PlanAdminRead(
            id=plan.id,  # type: ignore[arg-type]
            group_id=plan.group_id,
            transfer_enable=plan.transfer_enable,
            device_limit=plan.device_limit,
            name=plan.name,
            speed_limit=plan.speed_limit,
            show=plan.show,
            sort=plan.sort,
            renew=plan.renew,
            content=plan.content,
            month_price=plan.month_price,
            quarter_price=plan.quarter_price,
            half_year_price=plan.half_year_price,
            year_price=plan.year_price,
            two_year_price=plan.two_year_price,
            three_year_price=plan.three_year_price,
            onetime_price=plan.onetime_price,
            reset_price=plan.reset_price,
            reset_traffic_method=plan.reset_traffic_method,
            capacity_limit=plan.capacity_limit,
            count=counts.get(plan.id, 0),  # type: ignore[arg-type]
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    async def create(self, data: PlanCreate) -> PlanAdminRead:
        """创建套餐。"""
        plan = Plan(**data.model_dump())
        plan = await self.repo.create(plan)
        counts = await self.repo.count_active_users()
        return PlanAdminRead(
            id=plan.id,  # type: ignore[arg-type]
            group_id=plan.group_id,
            transfer_enable=plan.transfer_enable,
            device_limit=plan.device_limit,
            name=plan.name,
            speed_limit=plan.speed_limit,
            show=plan.show,
            sort=plan.sort,
            renew=plan.renew,
            content=plan.content,
            month_price=plan.month_price,
            quarter_price=plan.quarter_price,
            half_year_price=plan.half_year_price,
            year_price=plan.year_price,
            two_year_price=plan.two_year_price,
            three_year_price=plan.three_year_price,
            onetime_price=plan.onetime_price,
            reset_price=plan.reset_price,
            reset_traffic_method=plan.reset_traffic_method,
            capacity_limit=plan.capacity_limit,
            count=counts.get(plan.id, 0),  # type: ignore[arg-type]
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    async def update(self, plan_id: int, data: PlanUpdate) -> PlanAdminRead:
        """部分更新套餐。"""
        plan = await self.repo.get_by_id(plan_id)
        if plan is None:
            raise NotFoundException(f"套餐 {plan_id} 不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        plan = await self.repo.update(plan)
        counts = await self.repo.count_active_users()
        return PlanAdminRead(
            id=plan.id,  # type: ignore[arg-type]
            group_id=plan.group_id,
            transfer_enable=plan.transfer_enable,
            device_limit=plan.device_limit,
            name=plan.name,
            speed_limit=plan.speed_limit,
            show=plan.show,
            sort=plan.sort,
            renew=plan.renew,
            content=plan.content,
            month_price=plan.month_price,
            quarter_price=plan.quarter_price,
            half_year_price=plan.half_year_price,
            year_price=plan.year_price,
            two_year_price=plan.two_year_price,
            three_year_price=plan.three_year_price,
            onetime_price=plan.onetime_price,
            reset_price=plan.reset_price,
            reset_traffic_method=plan.reset_traffic_method,
            capacity_limit=plan.capacity_limit,
            count=counts.get(plan.id, 0),  # type: ignore[arg-type]
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    async def delete(self, plan_id: int) -> None:
        """安全删除套餐 —— 有订单或活跃用户时拒绝删除。"""
        if await self.repo.has_orders(plan_id):
            raise ConflictException("该套餐下存在订单，无法删除")
        if await self.repo.has_active_users(plan_id):
            raise ConflictException("该套餐下存在活跃用户，无法删除")
        plan = await self.repo.get_by_id(plan_id)
        if plan is None:
            raise NotFoundException(f"套餐 {plan_id} 不存在")
        await self.repo.delete(plan)
