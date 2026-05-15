"""邀请返利 Service。"""

import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.commission_log.dto import CommissionLogPublic, CommissionTransfer
from app.models.commission_log.entity import CommissionLog
from app.models.invite_code.dto import InviteCodeCreate, InviteCodePublic, InviteCodeRead, InviteCodeUpdate
from app.models.invite_code.entity import InviteCode
from app.models.order.entity import Order
from app.repositories.commission_log import CommissionLogRepository
from app.repositories.invite_code import InviteCodeRepository
from app.repositories.order import OrderRepository
from app.repositories.user import UserRepository
from app.services.log_event import create_log_event
from app.services.order import generate_trade_no
from app.services.setting import SettingService

_CODE_ALPHABET = string.ascii_uppercase + string.digits


class InviteService:
    """邀请码和佣金业务逻辑。"""

    def __init__(
        self,
        db: AsyncSession,
        invite_repo: InviteCodeRepository,
        commission_repo: CommissionLogRepository,
        user_repo: UserRepository,
        order_repo: OrderRepository,
        setting_service: SettingService,
    ):
        self.db = db
        self.invite_repo = invite_repo
        self.commission_repo = commission_repo
        self.user_repo = user_repo
        self.order_repo = order_repo
        self.setting_service = setting_service

    async def fetch(self, user_id: int) -> dict:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        codes = await self.invite_repo.list_by_user(user_id, status=0)
        rate = user.commission_rate or await self.setting_service.get_int("invite_commission", 10)
        registered_count = await self.user_repo.count_invited_users(user_id)
        paid_commission = await self.commission_repo.sum_by_invite_user(user_id)
        pending_commission = await self.order_repo.sum_pending_commission(user_id)
        return {
            "codes": [_invite_to_public(item) for item in codes],
            "stat": [registered_count, paid_commission, pending_commission, rate, user.commission_balance],
        }

    async def create_for_user(self, user_id: int) -> InviteCodeRead:
        limit = await self.setting_service.get_int("invite_gen_limit", 5)
        if await self.invite_repo.count_active_by_user(user_id) >= limit:
            raise BadRequestException("邀请码创建数量已达上限")
        item = InviteCode(user_id=user_id, code=await self._generate_code(), status=0)
        item = await self.invite_repo.create(item)
        return _invite_to_read(item)

    async def list_commission_logs(self, user_id: int, offset: int = 0, limit: int = 50) -> list[CommissionLogPublic]:
        logs = await self.commission_repo.list_by_invite_user(user_id, offset, limit)
        return [_commission_to_public(item) for item in logs]

    async def transfer_commission(self, user_id: int, data: CommissionTransfer) -> bool:
        if data.amount <= 0:
            raise BadRequestException("划转金额必须大于 0")
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        if data.amount > user.commission_balance:
            raise BadRequestException("佣金余额不足")
        user.commission_balance -= data.amount
        user.balance += data.amount
        await self.user_repo.update(user)
        await self.order_repo.create(
            Order(
                invite_user_id=user.invite_user_id,
                user_id=user_id,
                plan_id=0,
                period="deposit",
                trade_no=generate_trade_no(),
                callback_no="佣金划转 Commission transfer",
                total_amount=0,
                surplus_amount=data.amount,
                type=9,
                status=3,
            )
        )
        return True

    async def admin_list_invite_codes(self, offset: int = 0, limit: int = 50) -> list[InviteCodePublic]:
        items = await self.invite_repo.list_all(offset, limit)
        return [_invite_to_public(item) for item in items]

    async def admin_create_invite_code(self, data: InviteCodeCreate) -> InviteCodeRead:
        user_id = data.user_id
        if user_id is None:
            raise BadRequestException("user_id 不能为空")
        if await self.user_repo.get_by_id(user_id) is None:
            raise NotFoundException("用户不存在")
        code = data.code.strip().upper() if data.code else await self._generate_code()
        if await self.invite_repo.code_exists(code):
            raise ConflictException("邀请码已存在")
        item = InviteCode(user_id=user_id, code=code, status=data.status)
        item = await self.invite_repo.create(item)
        return _invite_to_read(item)

    async def admin_update_invite_code(self, invite_id: int, data: InviteCodeUpdate) -> InviteCodeRead:
        item = await self.invite_repo.get_by_id(invite_id)
        if item is None:
            raise NotFoundException("邀请码不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item = await self.invite_repo.update(item)
        return _invite_to_read(item)

    async def admin_delete_invite_code(self, invite_id: int) -> None:
        item = await self.invite_repo.get_by_id(invite_id)
        if item is None:
            raise NotFoundException("邀请码不存在")
        await self.invite_repo.delete(item)

    async def admin_list_commission_logs(self, offset: int = 0, limit: int = 50) -> list[CommissionLogPublic]:
        logs = await self.commission_repo.list_all(offset, limit)
        return [_commission_to_public(item) for item in logs]

    async def _generate_code(self, length: int = 8) -> str:
        for _ in range(100):
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
            if not await self.invite_repo.code_exists(code):
                return code
        raise ConflictException("邀请码生成失败，请重试")


class CommissionService:
    """订单佣金计算。"""

    def __init__(
        self,
        commission_repo: CommissionLogRepository,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        setting_service: SettingService,
    ):
        self.commission_repo = commission_repo
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.setting_service = setting_service

    async def calculate_for_order(self, order: Order) -> None:
        if order.id is None:
            return
        locked_order = await self.order_repo.get_by_id_for_update(order.id)
        if (
            locked_order is None
            or locked_order.status != 3
            or locked_order.plan_id == 0
            or locked_order.total_amount <= 0
            or locked_order.commission_status in (2, 3)
        ):
            return
        if await self.commission_repo.get_by_trade_no(locked_order.trade_no):
            locked_order.commission_status = 2
            await self.order_repo.update(locked_order)
            return
        locked_order.commission_status = 1

        user = await self.user_repo.get_by_id(locked_order.user_id)
        if user is None:
            return
        invite_user_id = locked_order.invite_user_id or user.invite_user_id
        if invite_user_id is None or invite_user_id == user.id:
            locked_order.commission_status = 3
            await self.order_repo.update(locked_order)
            return

        invite_user = await self.user_repo.get_by_id(invite_user_id)
        if invite_user is None:
            locked_order.commission_status = 3
            await self.order_repo.update(locked_order)
            return

        first_time_only = await self.setting_service.get_int("commission_first_time_enable", 1)
        if first_time_only and await self.order_repo.count_completed_plan_orders(locked_order.user_id) > 1:
            locked_order.commission_status = 3
            await self.order_repo.update(locked_order)
            return

        rate = invite_user.commission_rate or await self.setting_service.get_int("invite_commission", 10)
        amount = int(locked_order.total_amount * rate / 100)
        if amount <= 0:
            locked_order.commission_status = 3
            await self.order_repo.update(locked_order)
            return

        locked_order.invite_user_id = invite_user_id
        locked_order.commission_balance = amount
        locked_order.actual_commission_balance = amount
        locked_order.commission_status = 2
        invite_user.commission_balance += amount
        await self.user_repo.update(invite_user)
        await self.order_repo.update(locked_order)
        commission_log = await self.commission_repo.create(
            CommissionLog(
                invite_user_id=invite_user_id,
                user_id=locked_order.user_id,
                trade_no=locked_order.trade_no,
                order_amount=locked_order.total_amount,
                get_amount=amount,
            )
        )
        await create_log_event(
            self.commission_repo.db,
            category="commission",
            event="commission.granted",
            message="订单返佣已入账",
            actor_type="user",
            actor_id=invite_user_id,
            target_type="order",
            target_id=locked_order.trade_no,
            data={
                "commission_log_id": commission_log.id,
                "invite_user_id": invite_user_id,
                "user_id": locked_order.user_id,
                "trade_no": locked_order.trade_no,
                "order_amount": locked_order.total_amount,
                "get_amount": amount,
                "rate": rate,
            },
        )


def _invite_to_public(item: InviteCode) -> InviteCodePublic:
    return InviteCodePublic.model_validate(item, from_attributes=True)


def _invite_to_read(item: InviteCode) -> InviteCodeRead:
    return InviteCodeRead.model_validate(item, from_attributes=True)


def _commission_to_public(item: CommissionLog) -> CommissionLogPublic:
    return CommissionLogPublic.model_validate(item, from_attributes=True)
