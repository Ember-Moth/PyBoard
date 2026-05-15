"""优惠券 Service。"""

import secrets
import string
import time
from typing import Any

import orjson

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.coupon.dto import (
    CouponCheck,
    CouponCheckResult,
    CouponCreate,
    CouponGenerate,
    CouponPublic,
    CouponRead,
    CouponUpdate,
)
from app.models.coupon.entity import Coupon
from app.models.order.entity import Order
from app.repositories.coupon import CouponRepository

_CODE_ALPHABET = string.ascii_uppercase + string.digits


class CouponService:
    """优惠券业务逻辑。"""

    def __init__(self, repo: CouponRepository):
        self.repo = repo

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[CouponPublic]:
        items = await self.repo.list_all(offset, limit)
        return [_to_public(item) for item in items]

    async def get(self, coupon_id: int) -> CouponRead:
        item = await self.repo.get_by_id(coupon_id)
        if item is None:
            raise NotFoundException("优惠券不存在")
        return _to_read(item)

    async def create(self, data: CouponCreate) -> CouponRead:
        payload = data.model_dump()
        payload["code"] = _normalize_code(payload.get("code") or await self._generate_code())
        await self._ensure_code_available(payload["code"])
        payload["limit_plan_ids"] = _dump_optional_list(payload.get("limit_plan_ids"))
        payload["limit_period"] = _dump_optional_list(payload.get("limit_period"))
        self._validate_payload(payload)
        item = await self.repo.create(Coupon(**payload))
        return _to_read(item)

    async def update(self, coupon_id: int, data: CouponUpdate) -> CouponRead:
        item = await self.repo.get_by_id(coupon_id)
        if item is None:
            raise NotFoundException("优惠券不存在")
        updates = data.model_dump(exclude_unset=True)
        if "code" in updates and updates["code"] is not None:
            updates["code"] = _normalize_code(updates["code"])
            if updates["code"] != item.code:
                await self._ensure_code_available(updates["code"])
        for key in ("limit_plan_ids", "limit_period"):
            if key in updates:
                updates[key] = _dump_optional_list(updates[key])
        payload = item.model_dump()
        payload.update(updates)
        self._validate_payload(payload)
        for field, value in updates.items():
            setattr(item, field, value)
        item = await self.repo.update(item)
        return _to_read(item)

    async def delete(self, coupon_id: int) -> None:
        item = await self.repo.get_by_id(coupon_id)
        if item is None:
            raise NotFoundException("优惠券不存在")
        await self.repo.delete(item)

    async def generate(self, data: CouponGenerate) -> list[CouponRead]:
        if data.generate_count < 1 or data.generate_count > 500:
            raise BadRequestException("生成数量必须在 1 到 500 之间")
        created: list[CouponRead] = []
        for _ in range(data.generate_count):
            payload = data.model_dump(exclude={"generate_count"})
            payload["code"] = await self._generate_code()
            payload["limit_plan_ids"] = _dump_optional_list(payload.get("limit_plan_ids"))
            payload["limit_period"] = _dump_optional_list(payload.get("limit_period"))
            self._validate_payload(payload)
            item = await self.repo.create(Coupon(**payload))
            created.append(_to_read(item))
        return created

    async def toggle_show(self, coupon_id: int) -> CouponRead:
        item = await self.repo.get_by_id(coupon_id)
        if item is None:
            raise NotFoundException("优惠券不存在")
        item.show = not item.show
        item = await self.repo.update(item)
        return _to_read(item)

    async def check(self, user_id: int, data: CouponCheck) -> CouponCheckResult:
        coupon = await self.validate(
            code=data.code,
            user_id=user_id,
            plan_id=data.plan_id,
            period=data.period,
        )
        discount = None
        if data.amount is not None:
            discount = self.calculate_discount(coupon, data.amount)
        return CouponCheckResult(coupon=_to_read(coupon), discount_amount=discount)

    async def apply_to_order(self, order: Order, code: str) -> None:
        """校验并把优惠券应用到订单。

        这里不扣减库存。订单创建只是用户意图，真正消耗优惠券必须等订单
        支付完成并开通时在同一事务中执行，避免取消订单或未支付订单占用库存。
        """
        coupon = await self.validate(
            code=code,
            user_id=order.user_id,
            plan_id=order.plan_id,
            period=order.period,
        )
        discount = self.calculate_discount(coupon, order.total_amount)
        if discount <= 0:
            raise BadRequestException("优惠券不可用于当前订单")
        order.coupon_id = coupon.id
        order.discount_amount = discount
        order.total_amount = max(0, order.total_amount - discount)

    async def consume_for_paid_order(self, order: Order) -> None:
        """支付完成开通时锁定并扣减优惠券库存。"""
        if order.coupon_id is None:
            return
        coupon = await self.repo.get_by_id_for_update(order.coupon_id)
        if coupon is None:
            raise BadRequestException("优惠券无效")
        await self._validate_coupon(
            coupon=coupon,
            user_id=order.user_id,
            plan_id=order.plan_id,
            period=order.period,
            exclude_order_id=order.id,
        )
        discount_base = order.total_amount + (order.balance_amount or 0) + (order.discount_amount or 0)
        discount = self.calculate_discount(coupon, discount_base)
        if discount != (order.discount_amount or 0):
            raise BadRequestException("优惠券金额已变化，请重新下单")
        if coupon.limit_use is not None:
            coupon.limit_use -= 1
            await self.repo.update(coupon)

    async def validate(
        self,
        *,
        code: str,
        user_id: int,
        plan_id: int,
        period: str,
    ) -> Coupon:
        coupon = await self.repo.get_by_code(_normalize_code(code))
        await self._validate_coupon(coupon=coupon, user_id=user_id, plan_id=plan_id, period=period)
        return coupon

    async def _validate_coupon(
        self,
        *,
        coupon: Coupon | None,
        user_id: int,
        plan_id: int,
        period: str,
        exclude_order_id: int | None = None,
    ) -> None:
        if coupon is None or not coupon.show:
            raise BadRequestException("优惠券无效")
        now = int(time.time())
        if coupon.limit_use is not None and coupon.limit_use <= 0:
            raise BadRequestException("优惠券已被使用完")
        if now < coupon.started_at:
            raise BadRequestException("优惠券尚未开始")
        if now > coupon.ended_at:
            raise BadRequestException("优惠券已过期")
        plan_ids = _parse_optional_list(coupon.limit_plan_ids)
        if plan_ids and plan_id not in {int(item) for item in plan_ids}:
            raise BadRequestException("优惠券不可用于该套餐")
        periods = _parse_optional_list(coupon.limit_period)
        if periods and period not in {str(item) for item in periods}:
            raise BadRequestException("优惠券不可用于该周期")
        if coupon.limit_use_with_user is not None:
            used = await self.repo.count_user_used(coupon.id, user_id, exclude_order_id=exclude_order_id)  # type: ignore[arg-type]
            if used >= coupon.limit_use_with_user:
                raise BadRequestException("该优惠券已达到单用户使用上限")

    def calculate_discount(self, coupon: Coupon, amount: int) -> int:
        if amount <= 0:
            return 0
        if coupon.type == 1:
            discount = coupon.value
        elif coupon.type == 2:
            discount = int(amount * (coupon.value / 100))
        else:
            raise BadRequestException("未知优惠券类型")
        return max(0, min(amount, discount))

    async def _generate_code(self, length: int = 8) -> str:
        for _ in range(100):
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
            if not await self.repo.code_exists(code):
                return code
        raise ConflictException("优惠券码生成失败，请重试")

    async def _ensure_code_available(self, code: str) -> None:
        if await self.repo.code_exists(code):
            raise ConflictException("优惠券码已存在")

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        if payload["type"] not in (1, 2):
            raise BadRequestException("优惠券类型只支持 1=固定金额 或 2=百分比")
        if payload["value"] <= 0:
            raise BadRequestException("优惠券面值必须大于 0")
        if payload["started_at"] >= payload["ended_at"]:
            raise BadRequestException("优惠券结束时间必须晚于开始时间")


def _to_public(coupon: Coupon) -> CouponPublic:
    return CouponPublic.model_validate(coupon, from_attributes=True)


def _to_read(coupon: Coupon) -> CouponRead:
    return CouponRead.model_validate(coupon, from_attributes=True)


def _normalize_code(code: str) -> str:
    code = code.strip().upper()
    if not code:
        raise BadRequestException("优惠券码不能为空")
    return code


def _dump_optional_list(value: list[int] | list[str] | str | None) -> str | None:
    if value in (None, "", []):
        return None
    if isinstance(value, str):
        return value
    return orjson.dumps(value).decode()


def _parse_optional_list(value: str | None) -> list:
    if not value:
        return []
    try:
        parsed = orjson.loads(value)
    except orjson.JSONDecodeError:
        return [item.strip() for item in value.split(",") if item.strip()]
    return parsed if isinstance(parsed, list) else []
