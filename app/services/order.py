"""订单 Service 层 —— 订单业务逻辑。"""

import time
import uuid
from calendar import monthrange
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import AppException, BadRequestException, ConflictException, NotFoundException
from app.models.commission_log.entity import CommissionLog
from app.models.order.dto import AdminOrderAssign, AdminOrderUpdate, OrderCreate
from app.models.order.entity import Order
from app.payments import PaymentRequest, canonical_gateway_name, create_payment_gateway, route_gateway_name
from app.repositories.coupon import CouponRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.plan import PlanRepository
from app.repositories.user import UserRepository
from app.services.coupon import CouponService
from app.services.log_event import create_log_event
from app.services.setting import SettingService

PRICE_PERIODS = {
    "month_price",
    "quarter_price",
    "half_year_price",
    "year_price",
    "two_year_price",
    "three_year_price",
    "onetime_price",
    "reset_price",
}
PERIOD_MONTHS = {
    "month_price": 1,
    "quarter_price": 3,
    "half_year_price": 6,
    "year_price": 12,
    "two_year_price": 24,
    "three_year_price": 36,
}
NEVER_EXPIRES_AT = 4_102_444_800  # 2100-01-01 00:00:00 UTC


def generate_trade_no() -> str:
    """生成交易号。"""
    timestamp = str(int(time.time()))
    random_str = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"{timestamp}{random_str}"


def _is_user_active(expired_at: int | None) -> bool:
    """判断用户订阅是否有效。None 表示永久有效。"""
    return expired_at is None or expired_at > int(time.time())


def _add_months(timestamp: int, months: int) -> int:
    """按自然月延长 Unix 时间戳。"""
    base = max(timestamp or 0, int(time.time()))
    dt = datetime.fromtimestamp(base)
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return int(dt.replace(year=year, month=month, day=day).timestamp())


class OrderService:
    """订单业务逻辑。"""

    def __init__(self, db: AsyncSession, setting_service: SettingService):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.plan_repo = PlanRepository(db)
        self.user_repo = UserRepository(db)
        self.coupon_service = CouponService(CouponRepository(db))
        self.setting_service = setting_service

    # ---- 用户端 ----

    async def get_user_orders(self, user_id: int, status: int | None = None) -> list[Order]:
        """获取用户订单列表。"""
        return await self.order_repo.get_by_user_id(user_id, status)

    async def get_order_detail(self, trade_no: str, user_id: int) -> dict[str, Any]:
        """获取订单详情。"""
        order = await self.order_repo.get_by_trade_no(trade_no)
        if order is None or order.user_id != user_id:
            raise NotFoundException("订单不存在")

        plan = None
        if order.plan_id > 0:
            plan_entity = await self.plan_repo.get_by_id(order.plan_id)
            if plan_entity:
                plan = {
                    "id": plan_entity.id,
                    "name": plan_entity.name,
                    "month_price": plan_entity.month_price,
                    "quarter_price": plan_entity.quarter_price,
                    "year_price": plan_entity.year_price,
                    "onetime_price": plan_entity.onetime_price,
                }

        return {
            "order": order,
            "plan": plan,
        }

    async def create_order(self, user_id: int, data: OrderCreate) -> str:
        """创建订单。"""
        # 检查是否有待支付订单
        if await self.order_repo.has_pending_order(user_id):
            raise ConflictException("您有未支付的订单，请先支付或取消")

        # 获取用户
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")

        # 充值订单
        if data.plan_id == 0:
            if data.coupon_code:
                raise BadRequestException("充值订单不能使用优惠券")
            if data.deposit_amount is None or data.deposit_amount <= 0:
                raise BadRequestException("充值金额必须大于0")
            if data.deposit_amount >= 9999999:
                raise BadRequestException("充值金额过大")

            order = Order(
                user_id=user_id,
                plan_id=0,
                period="deposit",
                trade_no=generate_trade_no(),
                total_amount=data.deposit_amount,
                invite_user_id=user.invite_user_id,
                type=9,  # 充值
            )
            order = await self.order_repo.create(order)
            await self._log_order_event(
                order,
                "order.created",
                "订单已创建",
                actor_type="user",
                actor_id=user_id,
                data={"kind": "deposit", "total_amount": order.total_amount},
            )
            return order.trade_no

        # 获取套餐
        plan = await self.plan_repo.get_by_id(data.plan_id)
        if plan is None:
            raise NotFoundException("套餐不存在")

        if data.period not in PRICE_PERIODS:
            raise BadRequestException("不支持的支付周期")

        is_active = _is_user_active(user.expired_at)

        # 流量重置包只能由当前套餐的有效用户购买
        if data.period == "reset_price" and (not is_active or user.plan_id != plan.id):
            raise BadRequestException("当前订阅不可购买流量重置包")

        # 隐藏套餐仅允许当前持有且可续费的有效用户续费
        if data.period != "reset_price" and not plan.show:
            if not plan.renew or user.plan_id != plan.id or not is_active:
                raise BadRequestException("该套餐暂不可购买")

        if data.period != "reset_price" and user.plan_id == plan.id and not plan.renew:
            raise BadRequestException("该套餐暂不可购买")

        if _requires_capacity_slot(user.plan_id, user.expired_at, plan.id, data.period):
            await self._ensure_plan_capacity_available(plan.id, plan.capacity_limit)

        # 获取周期价格
        period_price = getattr(plan, data.period)
        if period_price is None or period_price < 0:
            raise BadRequestException("不支持的支付周期")

        # 创建订单
        total_amount = period_price
        balance_amount = None

        order = Order(
            user_id=user_id,
            invite_user_id=user.invite_user_id,
            plan_id=data.plan_id,
            period=data.period,
            trade_no=generate_trade_no(),
            total_amount=total_amount,
            type=self._determine_order_type(user.plan_id, user.expired_at, plan.id, data.period),
        )

        # 优惠券抵扣在余额抵扣之前计算，避免余额支付影响优惠金额。
        if data.coupon_code:
            await self.coupon_service.apply_to_order(order, data.coupon_code)
            total_amount = order.total_amount

        # 余额抵扣
        if user.balance and user.balance > 0:
            if user.balance >= total_amount:
                balance_amount = total_amount
                total_amount = 0
            else:
                balance_amount = user.balance
                total_amount -= user.balance

        order.total_amount = total_amount
        order.balance_amount = balance_amount
        order = await self.order_repo.create(order)
        await self._log_order_event(
            order,
            "order.created",
            "订单已创建",
            actor_type="user",
            actor_id=user_id,
            data={
                "kind": "plan",
                "plan_id": order.plan_id,
                "period": order.period,
                "total_amount": order.total_amount,
                "balance_amount": order.balance_amount,
                "discount_amount": order.discount_amount,
                "coupon_id": order.coupon_id,
            },
        )

        return order.trade_no

    async def checkout(self, user_id: int, trade_no: str, method: int) -> dict[str, Any]:
        """订单结账。"""
        order = await self.order_repo.get_pending_by_trade_no(trade_no, user_id)
        if order is None:
            raise NotFoundException("订单不存在或已支付")

        # 零元订单直接开通
        if order.total_amount <= 0:
            await self._log_order_event(
                order,
                "order.checkout",
                "订单已提交结账",
                actor_type="user",
                actor_id=user_id,
                data={"zero_amount": True},
            )
            await self._process_paid_order(order, actor_type="user", actor_id=user_id)
            return {"type": -1, "data": True}

        # 获取支付方式
        payment = await self.payment_repo.get_enabled_by_id(method)
        if payment is None:
            raise NotFoundException("支付方式不可用")

        # 计算手续费
        handling_amount = 0
        if payment.handling_fee_fixed:
            handling_amount += payment.handling_fee_fixed
        if payment.handling_fee_percent:
            handling_amount += int(order.total_amount * payment.handling_fee_percent / 100)

        if handling_amount > 0:
            order.handling_amount = handling_amount

        order.payment_id = method
        await self.order_repo.update(order)

        gateway = create_payment_gateway(payment.payment, payment.config)

        app_url = await self.setting_service.get_str("app_url", "")
        notify_domain = payment.notify_domain.rstrip("/") if payment.notify_domain else app_url
        notify_url = f"{notify_domain}/notify/{route_gateway_name(payment.payment)}/{payment.uuid}"
        return_url = f"{app_url}/#/order/{trade_no}"

        total_amount = order.total_amount + (order.handling_amount or 0)
        result = gateway.pay(
            PaymentRequest(
                trade_no=order.trade_no,
                total_amount=total_amount,
                notify_url=notify_url,
                return_url=return_url,
                user_id=order.user_id,
            )
        )

        await self._log_order_event(
            order,
            "order.checkout",
            "订单已提交结账",
            actor_type="user",
            actor_id=user_id,
            data={
                "payment_id": method,
                "handling_amount": order.handling_amount,
                "total_amount": total_amount,
            },
        )
        return result

    async def check_order_status(self, trade_no: str, user_id: int) -> int:
        """检查订单状态。"""
        order = await self.order_repo.get_by_trade_no(trade_no)
        if order is None or order.user_id != user_id:
            raise NotFoundException("订单不存在")
        return order.status

    async def cancel_order(self, trade_no: str, user_id: int) -> bool:
        """取消订单。"""
        order = await self.order_repo.get_by_trade_no(trade_no)
        if order is None or order.user_id != user_id:
            raise NotFoundException("订单不存在")

        if order.status != 0:
            raise BadRequestException("只能取消待支付订单")

        order.status = 2
        await self.order_repo.update(order)
        await self._log_order_event(
            order,
            "order.cancelled",
            "订单已取消",
            actor_type="user",
            actor_id=user_id,
        )

        return True

    # ---- 支付回调 ----

    async def handle_payment_notify(
        self,
        gateway_name: str,
        payment_uuid: str,
        params: dict[str, Any],
    ) -> str:
        """处理支付回调。"""
        payment = await self.payment_repo.get_by_uuid(payment_uuid)
        if payment is None:
            return "fail"
        if not payment.enable:
            return "fail"

        try:
            if canonical_gateway_name(gateway_name) != canonical_gateway_name(payment.payment):
                return "fail"
            gateway = create_payment_gateway(payment.payment, payment.config)
        except AppException:
            return "fail"

        # 验证签名
        notify = gateway.verify_notify(params)
        if not notify.success:
            return "fail"

        # 获取订单
        order = await self.order_repo.get_by_trade_no(notify.trade_no)
        if order is None:
            return "fail"

        if order.payment_id != payment.id:
            return "fail"

        expected_amount = order.total_amount + (order.handling_amount or 0)
        if notify.paid_amount != expected_amount:
            return "fail"

        if order.status not in (0, 1):
            return "success"

        # 处理订单
        try:
            await self._process_paid_order(order, callback_no=notify.callback_no, actor_type="system")
        except AppException:
            await self.db.rollback()
            return "fail"

        return "success"

    # ---- 管理端 ----

    async def list_orders(self, offset: int = 0, limit: int = 50) -> list[Order]:
        """获取订单列表（管理端）。"""
        return await self.order_repo.get_all(offset, limit)

    async def get_order(self, order_id: int) -> Order:
        """获取订单详情（管理端）。"""
        order = await self.order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundException("订单不存在")
        return order

    async def get_order_detail_admin(self, order_id: int) -> dict[str, Any]:
        """获取管理端订单详情，带佣金记录。"""
        order = await self.get_order(order_id)
        result = await self.db.execute(select(CommissionLog).where(CommissionLog.trade_no == order.trade_no))
        return {
            "order": order,
            "commission_log": list(result.scalars().all()),
        }

    async def admin_update_order(self, data: AdminOrderUpdate, actor_id: int | None = None) -> bool:
        """管理端更新订单字段。"""
        order = await self.order_repo.get_by_trade_no(data.trade_no)
        if order is None:
            raise NotFoundException("订单不存在")
        updates = data.model_dump(exclude_unset=True)
        updates.pop("trade_no", None)
        for field, value in updates.items():
            setattr(order, field, value)
        await self.order_repo.update(order)
        await self._log_order_event(
            order,
            "order.updated",
            "管理员更新订单",
            actor_type="admin",
            actor_id=actor_id,
            data={"fields": sorted(updates)},
        )
        return True

    async def admin_mark_paid(self, trade_no: str, actor_id: int | None = None) -> bool:
        """管理端手动标记待支付订单为已支付并开通。"""
        order = await self.order_repo.get_by_trade_no(trade_no)
        if order is None:
            raise NotFoundException("订单不存在")
        if order.status != 0:
            raise BadRequestException("只能操作待支付订单")
        await self._process_paid_order(
            order,
            callback_no="manual_operation",
            actor_type="admin",
            actor_id=actor_id,
        )
        await self._log_order_event(
            order,
            "order.admin_paid",
            "管理员手动标记订单已支付",
            actor_type="admin",
            actor_id=actor_id,
        )
        return True

    async def admin_cancel_order(self, trade_no: str, actor_id: int | None = None) -> bool:
        """管理端取消待支付订单。"""
        order = await self.order_repo.get_by_trade_no(trade_no)
        if order is None:
            raise NotFoundException("订单不存在")
        if order.status != 0:
            raise BadRequestException("只能操作待支付订单")
        order.status = 2
        await self.order_repo.update(order)
        await self._log_order_event(
            order,
            "order.cancelled",
            "管理员取消订单",
            actor_type="admin",
            actor_id=actor_id,
        )
        return True

    async def admin_assign_order(self, data: AdminOrderAssign, actor_id: int | None = None) -> str:
        """管理端给用户分配套餐订单。"""
        user = await self.user_repo.get_by_email(data.email)
        if user is None:
            raise NotFoundException("用户不存在")
        plan = await self.plan_repo.get_by_id(data.plan_id)
        if plan is None:
            raise NotFoundException("套餐不存在")
        if await self.order_repo.has_pending_order(user.id):  # type: ignore[arg-type]
            raise ConflictException("该用户还有待支付订单，无法分配")
        order = Order(
            invite_user_id=user.invite_user_id,
            user_id=user.id,  # type: ignore[arg-type]
            plan_id=plan.id,  # type: ignore[arg-type]
            period=data.period,
            trade_no=generate_trade_no(),
            total_amount=data.total_amount,
            type=self._determine_order_type(user.plan_id, user.expired_at, plan.id, data.period),
        )
        order = await self.order_repo.create(order)
        await self._log_order_event(
            order,
            "order.created",
            "管理员分配订单",
            actor_type="admin",
            actor_id=actor_id,
            data={
                "kind": "assigned",
                "plan_id": order.plan_id,
                "period": order.period,
                "total_amount": order.total_amount,
            },
        )
        return order.trade_no

    # ---- 内部方法 ----

    async def _process_paid_order(
        self,
        order: Order,
        callback_no: str | None = None,
        actor_type: str = "system",
        actor_id: int | None = None,
    ) -> None:
        """处理已支付订单：扣余额、充值、开通套餐或重置流量。

        订单开通是强一致业务。这里在当前事务内重新锁定订单行，确保并发回调、
        定时扫描和人工操作不会重复开通同一笔订单。
        """
        locked_order = (
            await self.order_repo.get_by_id_for_update(int(order.id))
            if order.id is not None
            else await self.order_repo.get_by_trade_no_for_update(order.trade_no)
        )
        if locked_order is None:
            raise NotFoundException("订单不存在")
        if locked_order.status == 3:
            return
        if locked_order.status not in (0, 1):
            return
        locked_order.status = 1
        if callback_no is not None:
            locked_order.callback_no = callback_no

        user = await self.user_repo.get_by_id_for_update(locked_order.user_id)
        if user is None:
            raise NotFoundException("用户不存在")

        if locked_order.period == "deposit" or locked_order.plan_id == 0:
            user.balance = (user.balance or 0) + locked_order.total_amount
            user.balance += await self._deposit_bonus(locked_order.total_amount)
            await self.user_repo.update(user)
        else:
            plan = await self.plan_repo.get_by_id_for_update(locked_order.plan_id)
            if plan is None:
                raise NotFoundException("套餐不存在")

            if _requires_capacity_slot(user.plan_id, user.expired_at, plan.id, locked_order.period):
                await self._ensure_plan_capacity_available(plan.id, plan.capacity_limit)

            if locked_order.coupon_id is not None and (locked_order.discount_amount or 0) > 0:
                await self.coupon_service.consume_for_paid_order(locked_order)

            if locked_order.balance_amount and locked_order.balance_amount > 0:
                if (user.balance or 0) < locked_order.balance_amount:
                    raise BadRequestException("用户余额不足")
                user.balance = (user.balance or 0) - locked_order.balance_amount

            if locked_order.period == "reset_price":
                user.u = 0
                user.d = 0
            elif locked_order.period == "onetime_price":
                user.u = 0
                user.d = 0
                user.transfer_enable = plan.transfer_enable
                user.device_limit = plan.device_limit
                user.plan_id = plan.id
                user.group_id = plan.group_id
                user.speed_limit = plan.speed_limit
                user.expired_at = NEVER_EXPIRES_AT
            else:
                months = PERIOD_MONTHS.get(locked_order.period)
                if months is None:
                    raise BadRequestException("不支持的支付周期")
                if locked_order.type == 1 or not _is_user_active(user.expired_at):
                    user.u = 0
                    user.d = 0
                user.transfer_enable = plan.transfer_enable
                user.device_limit = plan.device_limit
                user.plan_id = plan.id
                user.group_id = plan.group_id
                user.speed_limit = plan.speed_limit
                user.expired_at = _add_months(user.expired_at or 0, months)

            await self.user_repo.update(user)

        # 更新订单状态
        locked_order.status = 3  # 已完成
        locked_order.paid_at = int(time.time())
        await self.order_repo.update(locked_order)

        if locked_order.plan_id > 0:
            from app.repositories.commission_log import CommissionLogRepository
            from app.services.commission import CommissionService

            commission_service = CommissionService(
                CommissionLogRepository(self.db),
                self.order_repo,
                self.user_repo,
                self.setting_service,
            )
            await commission_service.calculate_for_order(locked_order)

        await self._log_order_event(
            locked_order,
            "order.completed",
            "订单已支付并完成开通",
            actor_type=actor_type,
            actor_id=actor_id,
            data={
                "callback_no": callback_no,
                "plan_id": locked_order.plan_id,
                "period": locked_order.period,
                "total_amount": locked_order.total_amount,
                "balance_amount": locked_order.balance_amount,
                "discount_amount": locked_order.discount_amount,
                "payment_id": locked_order.payment_id,
            },
        )

    def _determine_order_type(
        self,
        user_plan_id: int | None,
        expired_at: int | None,
        plan_id: int | None,
        period: str,
    ) -> int:
        """根据用户当前订阅推断订单类型。"""
        if period == "reset_price":
            return 4
        if user_plan_id is not None and plan_id != user_plan_id and _is_user_active(expired_at):
            return 3
        if user_plan_id == plan_id and _is_user_active(expired_at):
            return 2
        return 1

    async def _deposit_bonus(self, total_amount: int) -> int:
        """按 deposit_bounus 配置计算充值赠送金额。"""
        tiers = await self.setting_service.get_json("deposit_bounus", [])
        if not isinstance(tiers, list):
            return 0
        bonus = 0
        for tier in tiers:
            try:
                amount, value = str(tier).split(":", 1)
                amount_cents = int(float(amount) * 100)
                value_cents = int(float(value) * 100)
            except (TypeError, ValueError):
                continue
            if total_amount >= amount_cents:
                bonus = max(bonus, value_cents)
        return bonus

    async def _ensure_plan_capacity_available(self, plan_id: int | None, capacity_limit: int | None) -> None:
        """检查套餐是否仍有容量。"""
        if plan_id is None or capacity_limit is None or capacity_limit <= 0:
            return
        counts = await self.plan_repo.count_active_users()
        if counts.get(plan_id, 0) >= capacity_limit:
            raise BadRequestException("当前套餐已售罄")

    async def _log_order_event(
        self,
        order: Order,
        event: str,
        message: str,
        *,
        actor_type: str,
        actor_id: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        await create_log_event(
            self.db,
            category="audit",
            event=event,
            message=message,
            actor_type=actor_type,
            actor_id=actor_id,
            target_type="order",
            target_id=order.trade_no,
            data=data,
        )


def _requires_capacity_slot(
    user_plan_id: int | None,
    expired_at: int | None,
    plan_id: int | None,
    period: str,
) -> bool:
    """判断这笔订单是否会新增一个占用套餐容量的活跃用户。"""
    if period == "reset_price":
        return False
    return not (user_plan_id == plan_id and _is_user_active(expired_at))
