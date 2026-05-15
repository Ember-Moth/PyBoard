"""Giftcard DTO，接口视图，不做持久化。"""

from sqlmodel import SQLModel


class GiftcardPublic(SQLModel):
    """礼品卡列表公开视图。"""

    id: int
    code: str
    name: str
    type: int
    value: int | None
    plan_id: int | None
    limit_use: int | None
    started_at: int
    ended_at: int
    created_at: int


class GiftcardRead(SQLModel):
    """礼品卡详情视图。"""

    id: int
    code: str
    name: str
    type: int
    value: int | None
    plan_id: int | None
    limit_use: int | None
    used_user_ids: str | None
    started_at: int
    ended_at: int
    created_at: int
    updated_at: int


class GiftcardCreate(SQLModel):
    """创建礼品卡。"""

    code: str | None = None
    name: str
    type: int
    value: int | None = None
    plan_id: int | None = None
    limit_use: int | None = None
    started_at: int
    ended_at: int


class GiftcardUpdate(SQLModel):
    """更新礼品卡。"""

    code: str | None = None
    name: str | None = None
    type: int | None = None
    value: int | None = None
    plan_id: int | None = None
    limit_use: int | None = None
    used_user_ids: str | None = None
    started_at: int | None = None
    ended_at: int | None = None


class GiftcardGenerate(SQLModel):
    """批量生成礼品卡。"""

    name: str
    type: int
    value: int | None = None
    plan_id: int | None = None
    limit_use: int | None = None
    started_at: int
    ended_at: int
    generate_count: int = 1


class GiftcardRedeem(SQLModel):
    """用户端兑换礼品卡。"""

    code: str


class GiftcardRedeemResult(SQLModel):
    """礼品卡兑换结果。"""

    type: int
    value: int | None
    plan_id: int | None
