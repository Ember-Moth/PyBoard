"""礼品卡 Service。"""

import secrets
import string
import time

import orjson
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.giftcard.dto import (
    GiftcardCreate,
    GiftcardGenerate,
    GiftcardPublic,
    GiftcardRead,
    GiftcardRedeemResult,
    GiftcardUpdate,
)
from app.models.giftcard.entity import Giftcard
from app.models.giftcard_redemption.entity import GiftcardRedemption
from app.repositories.giftcard import GiftcardRepository
from app.repositories.giftcard_redemption import GiftcardRedemptionRepository
from app.repositories.plan import PlanRepository
from app.repositories.user import UserRepository
from app.services.log_event import create_log_event

_CODE_ALPHABET = string.ascii_uppercase + string.digits
_GIB = 1024 * 1024 * 1024


class GiftcardService:
    """礼品卡业务逻辑。"""

    def __init__(
        self,
        repo: GiftcardRepository,
        redemption_repo: GiftcardRedemptionRepository,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
    ):
        self.repo = repo
        self.redemption_repo = redemption_repo
        self.user_repo = user_repo
        self.plan_repo = plan_repo

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[GiftcardPublic]:
        items = await self.repo.list_all(offset, limit)
        return [_to_public(item) for item in items]

    async def get(self, giftcard_id: int) -> GiftcardRead:
        item = await self.repo.get_by_id(giftcard_id)
        if item is None:
            raise NotFoundException("礼品卡不存在")
        return _to_read(item)

    async def create(self, data: GiftcardCreate) -> GiftcardRead:
        payload = data.model_dump()
        payload["code"] = _normalize_code(payload.get("code") or await self._generate_code())
        await self._ensure_code_available(payload["code"])
        self._validate_payload(payload)
        item = await self.repo.create(Giftcard(**payload))
        return _to_read(item)

    async def update(self, giftcard_id: int, data: GiftcardUpdate) -> GiftcardRead:
        item = await self.repo.get_by_id(giftcard_id)
        if item is None:
            raise NotFoundException("礼品卡不存在")
        updates = data.model_dump(exclude_unset=True)
        if "code" in updates and updates["code"] is not None:
            updates["code"] = _normalize_code(updates["code"])
            if updates["code"] != item.code:
                await self._ensure_code_available(updates["code"])
        payload = item.model_dump()
        payload.update(updates)
        self._validate_payload(payload)
        for field, value in updates.items():
            setattr(item, field, value)
        item = await self.repo.update(item)
        return _to_read(item)

    async def delete(self, giftcard_id: int) -> None:
        item = await self.repo.get_by_id(giftcard_id)
        if item is None:
            raise NotFoundException("礼品卡不存在")
        await self.repo.delete(item)

    async def generate(self, data: GiftcardGenerate) -> list[GiftcardRead]:
        if data.generate_count < 1 or data.generate_count > 500:
            raise BadRequestException("生成数量必须在 1 到 500 之间")
        created: list[GiftcardRead] = []
        for _ in range(data.generate_count):
            payload = data.model_dump(exclude={"generate_count"})
            payload["code"] = await self._generate_code()
            self._validate_payload(payload)
            item = await self.repo.create(Giftcard(**payload))
            created.append(_to_read(item))
        return created

    async def redeem(self, user_id: int, code: str) -> GiftcardRedeemResult:
        normalized_code = _normalize_code(code)
        giftcard = await self.repo.get_by_code_for_update(normalized_code)
        if giftcard is None:
            raise BadRequestException("礼品卡不存在")
        user = await self.user_repo.get_by_id_for_update(user_id)
        if user is None:
            raise NotFoundException("用户不存在")

        now = int(time.time())
        if now < giftcard.started_at:
            raise BadRequestException("礼品卡尚未生效")
        if now > giftcard.ended_at:
            raise BadRequestException("礼品卡已过期")
        if giftcard.limit_use is not None and giftcard.limit_use <= 0:
            raise BadRequestException("礼品卡使用次数已耗尽")

        if giftcard.id is None:
            raise BadRequestException("礼品卡不存在")
        redemption = await self.redemption_repo.get_by_giftcard_and_user(giftcard.id, user_id)
        if redemption is not None:
            raise BadRequestException("该礼品卡已被当前用户使用")

        used_user_ids = _parse_used_users(giftcard.used_user_ids)
        if user_id in used_user_ids:
            raise BadRequestException("该礼品卡已被当前用户使用")

        value = giftcard.value or 0
        if giftcard.type == 1:
            user.balance += value
        elif giftcard.type == 2:
            if value <= 0:
                raise BadRequestException("礼品卡时长必须大于 0")
            user.expired_at = max(user.expired_at or 0, now) + value * 86400
        elif giftcard.type == 3:
            if value <= 0:
                raise BadRequestException("礼品卡流量必须大于 0")
            user.transfer_enable += value * _GIB
        elif giftcard.type == 4:
            user.u = 0
            user.d = 0
        elif giftcard.type == 5:
            await self._apply_plan_giftcard(giftcard, user, now)
        else:
            raise BadRequestException("未知礼品卡类型")

        used_user_ids.append(user_id)
        giftcard.used_user_ids = orjson.dumps(used_user_ids).decode()
        if giftcard.limit_use is not None:
            giftcard.limit_use -= 1
        await self.user_repo.update(user)
        await self.repo.update(giftcard)
        try:
            await self.redemption_repo.create(
                GiftcardRedemption(
                    giftcard_id=giftcard.id,
                    user_id=user_id,
                    code=giftcard.code,
                    type=giftcard.type,
                    value=giftcard.value,
                    plan_id=giftcard.plan_id,
                )
            )
        except IntegrityError as exc:
            raise BadRequestException("该礼品卡已被当前用户使用") from exc
        await create_log_event(
            self.repo.db,
            category="audit",
            event="giftcard.redeemed",
            message="礼品卡已兑换",
            actor_type="user",
            actor_id=user_id,
            target_type="giftcard",
            target_id=str(giftcard.id),
            data={
                "code": giftcard.code,
                "type": giftcard.type,
                "value": giftcard.value,
                "plan_id": giftcard.plan_id,
            },
        )
        return GiftcardRedeemResult(type=giftcard.type, value=giftcard.value, plan_id=giftcard.plan_id)

    async def _apply_plan_giftcard(self, giftcard: Giftcard, user, now: int) -> None:
        if user.plan_id is not None and user.expired_at and user.expired_at > now:
            raise BadRequestException("当前订阅未过期，不能使用套餐礼品卡")
        if giftcard.plan_id is None:
            raise BadRequestException("套餐礼品卡未绑定套餐")
        plan = await self.plan_repo.get_by_id_for_update(giftcard.plan_id)
        if plan is None:
            raise BadRequestException("礼品卡绑定的套餐不存在")
        user.plan_id = plan.id
        user.group_id = plan.group_id
        user.transfer_enable = plan.transfer_enable
        user.device_limit = plan.device_limit
        user.speed_limit = plan.speed_limit
        user.u = 0
        user.d = 0
        if giftcard.value == 0:
            user.expired_at = 4_102_444_800
        else:
            user.expired_at = now + (giftcard.value or 0) * 86400

    async def _generate_code(self, length: int = 16) -> str:
        for _ in range(100):
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
            if not await self.repo.code_exists(code):
                return code
        raise ConflictException("礼品卡码生成失败，请重试")

    async def _ensure_code_available(self, code: str) -> None:
        if await self.repo.code_exists(code):
            raise ConflictException("礼品卡码已存在")

    def _validate_payload(self, payload: dict) -> None:
        if payload["type"] not in (1, 2, 3, 4, 5):
            raise BadRequestException("礼品卡类型只支持 1=余额 2=时长 3=流量 4=重置 5=套餐")
        if payload["started_at"] >= payload["ended_at"]:
            raise BadRequestException("礼品卡结束时间必须晚于开始时间")
        if payload["type"] == 5 and payload.get("plan_id") is None:
            raise BadRequestException("套餐礼品卡必须绑定套餐")


def _to_public(giftcard: Giftcard) -> GiftcardPublic:
    return GiftcardPublic.model_validate(giftcard, from_attributes=True)


def _to_read(giftcard: Giftcard) -> GiftcardRead:
    return GiftcardRead.model_validate(giftcard, from_attributes=True)


def _normalize_code(code: str) -> str:
    code = code.strip().upper()
    if not code:
        raise BadRequestException("礼品卡码不能为空")
    return code


def _parse_used_users(value: str | None) -> list[int]:
    if not value:
        return []
    try:
        parsed = orjson.loads(value)
    except orjson.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [int(item) for item in parsed if isinstance(item, int | str) and str(item).isdigit()]
