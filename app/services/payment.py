"""支付方式 Service 层 —— 支付方式管理。"""

import uuid

from app.core.exceptions import ConflictException, NotFoundException
from app.models.order.dto import PaymentMethodPublic
from app.models.payment.dto import PaymentCreate, PaymentUpdate
from app.models.payment.entity import Payment
from app.payments import (
    canonical_gateway_name,
    list_payment_gateways,
    validate_gateway_config,
)
from app.repositories.payment import PaymentRepository


class PaymentService:
    """支付方式管理业务逻辑。"""

    def __init__(self, payment_repo: PaymentRepository):
        self.payment_repo = payment_repo

    async def get_enabled_methods(self) -> list[PaymentMethodPublic]:
        """获取可用支付方式列表。"""
        methods = await self.payment_repo.get_enabled_methods()
        return [
            PaymentMethodPublic(
                id=m.id,
                name=m.name,
                payment=m.payment,
                icon=m.icon,
                handling_fee_fixed=m.handling_fee_fixed,
                handling_fee_percent=m.handling_fee_percent,
            )
            for m in methods
        ]

    # ---- 管理端 ----

    def list_gateways(self) -> list[dict]:
        """获取后端已注册的支付网关列表。"""
        return list_payment_gateways()

    async def list_payments(self, offset: int = 0, limit: int = 50) -> list[Payment]:
        """获取所有支付方式。"""
        return await self.payment_repo.get_all(offset, limit)

    async def get_payment(self, payment_id: int) -> Payment:
        """获取支付方式详情。"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundException("支付方式不存在")
        return payment

    async def create_payment(self, data: PaymentCreate) -> Payment:
        """创建支付方式。"""
        config = validate_gateway_config(data.payment, data.config)
        payment = Payment(
            uuid=str(uuid.uuid4()).replace("-", ""),
            payment=canonical_gateway_name(data.payment),
            name=data.name,
            icon=data.icon,
            config=config,
            notify_domain=data.notify_domain,
            handling_fee_fixed=data.handling_fee_fixed,
            handling_fee_percent=data.handling_fee_percent,
            enable=data.enable,
            sort=data.sort,
        )
        return await self.payment_repo.create(payment)

    async def update_payment(self, payment_id: int, data: PaymentUpdate) -> Payment:
        """更新支付方式。"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundException("支付方式不存在")

        updates = data.model_dump(exclude_unset=True)
        gateway_name = updates.get("payment", payment.payment)
        if "payment" in updates or "config" in updates:
            updates["config"] = validate_gateway_config(gateway_name, updates.get("config", payment.config))
            updates["payment"] = canonical_gateway_name(gateway_name)

        for field, value in updates.items():
            setattr(payment, field, value)

        return await self.payment_repo.update(payment)

    async def delete_payment(self, payment_id: int) -> bool:
        """删除支付方式。"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundException("支付方式不存在")
        if await self.payment_repo.has_orders(payment_id):
            raise ConflictException("该支付方式已被订单引用，无法删除")

        await self.payment_repo.delete(payment)
        return True
