"""Admin HTML UI 表单到 DTO 的转换。"""

from typing import Any

import orjson

from app.admin_ui.deps import as_bool, blank_none, float_or_none, int_or_none, required_int
from app.models.invite_code.dto import InviteCodeCreate, InviteCodeUpdate
from app.models.coupon.dto import CouponCreate, CouponGenerate, CouponUpdate
from app.models.giftcard.dto import GiftcardCreate, GiftcardGenerate, GiftcardUpdate
from app.models.knowledge.dto import KnowledgeCreate, KnowledgeUpdate
from app.models.mail.dto import MailSend
from app.models.notice.dto import NoticeCreate, NoticeUpdate
from app.models.order.dto import AdminOrderAssign
from app.models.payment.dto import PaymentCreate, PaymentUpdate
from app.models.plan.dto import PlanCreate, PlanUpdate
from app.models.server_group.dto import ServerGroupCreate, ServerGroupUpdate
from app.models.server_route.dto import ServerRouteCreate, ServerRouteUpdate
from app.models.server_v2node.dto import ServerV2NodeCreate, ServerV2NodeUpdate
from app.models.ticket.dto import TicketReply
from app.models.user.dto import UserUpdate


def user_update_from_form(form: dict[str, str]) -> UserUpdate:
    return UserUpdate(
        email=blank_none(form.get("email")),
        password=blank_none(form.get("password")),
        balance=int_or_none(form.get("balance")),
        transfer_enable=int_or_none(form.get("transfer_enable")),
        device_limit=int_or_none(form.get("device_limit")),
        speed_limit=int_or_none(form.get("speed_limit")),
        group_id=int_or_none(form.get("group_id")),
        plan_id=int_or_none(form.get("plan_id")),
        discount=int_or_none(form.get("discount")),
        commission_rate=int_or_none(form.get("commission_rate")),
        expired_at=int_or_none(form.get("expired_at")),
        remarks=blank_none(form.get("remarks")),
        banned=as_bool(form.get("banned")),
        is_admin=as_bool(form.get("is_admin")),
        is_staff=as_bool(form.get("is_staff")),
    )


def plan_create_from_form(form: dict[str, str]) -> PlanCreate:
    return PlanCreate(
        name=str(form.get("name") or ""),
        group_id=required_int(form.get("group_id")),
        transfer_enable=required_int(form.get("transfer_enable")),
        device_limit=int_or_none(form.get("device_limit")),
        speed_limit=int_or_none(form.get("speed_limit")),
        show=as_bool(form.get("show")),
        sort=int_or_none(form.get("sort")),
        renew=as_bool(form.get("renew")),
        content=blank_none(form.get("content")),
        month_price=int_or_none(form.get("month_price")),
        quarter_price=int_or_none(form.get("quarter_price")),
        half_year_price=int_or_none(form.get("half_year_price")),
        year_price=int_or_none(form.get("year_price")),
        two_year_price=int_or_none(form.get("two_year_price")),
        three_year_price=int_or_none(form.get("three_year_price")),
        onetime_price=int_or_none(form.get("onetime_price")),
        reset_price=int_or_none(form.get("reset_price")),
        reset_traffic_method=int_or_none(form.get("reset_traffic_method")),
        capacity_limit=int_or_none(form.get("capacity_limit")),
    )


def notice_create_from_form(form: dict[str, str]) -> NoticeCreate:
    return NoticeCreate(
        title=str(form.get("title") or ""),
        content=str(form.get("content") or ""),
        show=as_bool(form.get("show")),
        img_url=blank_none(form.get("img_url")),
        tags=blank_none(form.get("tags")),
    )


def notice_update_from_form(form: dict[str, str]) -> NoticeUpdate:
    return NoticeUpdate(
        title=blank_none(form.get("title")),
        content=blank_none(form.get("content")),
        show=as_bool(form.get("show")),
        img_url=blank_none(form.get("img_url")),
        tags=blank_none(form.get("tags")),
    )


def knowledge_create_from_form(form: dict[str, str]) -> KnowledgeCreate:
    return KnowledgeCreate(
        language=str(form.get("language") or ""),
        category=str(form.get("category") or ""),
        title=str(form.get("title") or ""),
        body=str(form.get("body") or ""),
        sort=int_or_none(form.get("sort")),
        show=as_bool(form.get("show")),
    )


def knowledge_update_from_form(form: dict[str, str]) -> KnowledgeUpdate:
    return KnowledgeUpdate(
        language=blank_none(form.get("language")),
        category=blank_none(form.get("category")),
        title=blank_none(form.get("title")),
        body=blank_none(form.get("body")),
        sort=int_or_none(form.get("sort")),
        show=as_bool(form.get("show")),
    )


def coupon_create_from_form(form: dict[str, str]) -> CouponCreate:
    return CouponCreate(
        code=blank_none(form.get("code")),
        name=str(form.get("name") or ""),
        type=required_int(form.get("type")),
        value=required_int(form.get("value")),
        show=as_bool(form.get("show")),
        limit_use=int_or_none(form.get("limit_use")),
        limit_use_with_user=int_or_none(form.get("limit_use_with_user")),
        limit_plan_ids=blank_none(form.get("limit_plan_ids")),
        limit_period=blank_none(form.get("limit_period")),
        started_at=required_int(form.get("started_at")),
        ended_at=required_int(form.get("ended_at")),
    )


def coupon_update_from_form(form: dict[str, str]) -> CouponUpdate:
    return CouponUpdate(
        code=blank_none(form.get("code")),
        name=blank_none(form.get("name")),
        type=int_or_none(form.get("type")),
        value=int_or_none(form.get("value")),
        show=as_bool(form.get("show")),
        limit_use=int_or_none(form.get("limit_use")),
        limit_use_with_user=int_or_none(form.get("limit_use_with_user")),
        limit_plan_ids=blank_none(form.get("limit_plan_ids")),
        limit_period=blank_none(form.get("limit_period")),
        started_at=int_or_none(form.get("started_at")),
        ended_at=int_or_none(form.get("ended_at")),
    )


def coupon_generate_from_form(form: dict[str, str]) -> CouponGenerate:
    return CouponGenerate(
        name=str(form.get("name") or ""),
        type=required_int(form.get("type")),
        value=required_int(form.get("value")),
        generate_count=required_int(form.get("generate_count")),
        show=as_bool(form.get("show")),
        limit_use=int_or_none(form.get("limit_use")),
        limit_use_with_user=int_or_none(form.get("limit_use_with_user")),
        limit_plan_ids=blank_none(form.get("limit_plan_ids")),
        limit_period=blank_none(form.get("limit_period")),
        started_at=required_int(form.get("started_at")),
        ended_at=required_int(form.get("ended_at")),
    )


def giftcard_create_from_form(form: dict[str, str]) -> GiftcardCreate:
    return GiftcardCreate(
        code=blank_none(form.get("code")),
        name=str(form.get("name") or ""),
        type=required_int(form.get("type")),
        value=int_or_none(form.get("value")),
        plan_id=int_or_none(form.get("plan_id")),
        limit_use=int_or_none(form.get("limit_use")),
        started_at=required_int(form.get("started_at")),
        ended_at=required_int(form.get("ended_at")),
    )


def giftcard_update_from_form(form: dict[str, str]) -> GiftcardUpdate:
    return GiftcardUpdate(
        code=blank_none(form.get("code")),
        name=blank_none(form.get("name")),
        type=int_or_none(form.get("type")),
        value=int_or_none(form.get("value")),
        plan_id=int_or_none(form.get("plan_id")),
        limit_use=int_or_none(form.get("limit_use")),
        used_user_ids=blank_none(form.get("used_user_ids")),
        started_at=int_or_none(form.get("started_at")),
        ended_at=int_or_none(form.get("ended_at")),
    )


def giftcard_generate_from_form(form: dict[str, str]) -> GiftcardGenerate:
    return GiftcardGenerate(
        name=str(form.get("name") or ""),
        type=required_int(form.get("type")),
        value=int_or_none(form.get("value")),
        plan_id=int_or_none(form.get("plan_id")),
        limit_use=int_or_none(form.get("limit_use")),
        started_at=required_int(form.get("started_at")),
        ended_at=required_int(form.get("ended_at")),
        generate_count=required_int(form.get("generate_count")),
    )


def plan_update_from_form(form: dict[str, str]) -> PlanUpdate:
    return PlanUpdate(
        name=blank_none(form.get("name")),
        group_id=int_or_none(form.get("group_id")),
        transfer_enable=int_or_none(form.get("transfer_enable")),
        device_limit=int_or_none(form.get("device_limit")),
        speed_limit=int_or_none(form.get("speed_limit")),
        show=as_bool(form.get("show")),
        sort=int_or_none(form.get("sort")),
        renew=as_bool(form.get("renew")),
        content=blank_none(form.get("content")),
        month_price=int_or_none(form.get("month_price")),
        quarter_price=int_or_none(form.get("quarter_price")),
        half_year_price=int_or_none(form.get("half_year_price")),
        year_price=int_or_none(form.get("year_price")),
        two_year_price=int_or_none(form.get("two_year_price")),
        three_year_price=int_or_none(form.get("three_year_price")),
        onetime_price=int_or_none(form.get("onetime_price")),
        reset_price=int_or_none(form.get("reset_price")),
        reset_traffic_method=int_or_none(form.get("reset_traffic_method")),
        capacity_limit=int_or_none(form.get("capacity_limit")),
    )


def payment_create_from_form(form: dict[str, str]) -> PaymentCreate:
    return PaymentCreate(
        payment=str(form.get("payment") or ""),
        name=str(form.get("name") or ""),
        icon=blank_none(form.get("icon")),
        config=str(form.get("config") or ""),
        notify_domain=blank_none(form.get("notify_domain")),
        handling_fee_fixed=int_or_none(form.get("handling_fee_fixed")),
        handling_fee_percent=float_or_none(form.get("handling_fee_percent")),
        enable=as_bool(form.get("enable")),
        sort=int_or_none(form.get("sort")),
    )


def payment_update_from_form(form: dict[str, str]) -> PaymentUpdate:
    return PaymentUpdate(
        payment=blank_none(form.get("payment")),
        name=blank_none(form.get("name")),
        icon=blank_none(form.get("icon")),
        config=blank_none(form.get("config")),
        notify_domain=blank_none(form.get("notify_domain")),
        handling_fee_fixed=int_or_none(form.get("handling_fee_fixed")),
        handling_fee_percent=float_or_none(form.get("handling_fee_percent")),
        enable=as_bool(form.get("enable")),
        sort=int_or_none(form.get("sort")),
    )


def order_assign_from_form(form: dict[str, str]) -> AdminOrderAssign:
    return AdminOrderAssign(
        email=str(form.get("email") or ""),
        plan_id=required_int(form.get("plan_id")),
        period=str(form.get("period") or ""),
        total_amount=int_or_none(form.get("total_amount")) or 0,
    )


def setting_group_values_from_form(form: dict[str, str]) -> dict[str, str | int | bool | dict | list]:
    values: dict[str, str | int | bool | dict | list] = {}
    for key, value in form.items():
        if key == "csrf_token" or key.startswith("_type_"):
            continue
        type_hint = form.get(f"_type_{key}") or "str"
        values[key] = _coerce_typed_value(value, type_hint)
    return values


def invite_code_create_from_form(form: dict[str, str]) -> InviteCodeCreate:
    return InviteCodeCreate(
        user_id=required_int(form.get("user_id")),
        code=blank_none(form.get("code")),
        status=int_or_none(form.get("status")) or 0,
    )


def invite_code_update_from_form(form: dict[str, str]) -> InviteCodeUpdate:
    return InviteCodeUpdate(
        status=int_or_none(form.get("status")),
        pv=int_or_none(form.get("pv")),
    )


def ticket_reply_from_form(form: dict[str, str]) -> TicketReply:
    return TicketReply(message=str(form.get("message") or ""))


def server_group_create_from_form(form: dict[str, str]) -> ServerGroupCreate:
    return ServerGroupCreate(name=str(form.get("name") or "").strip())


def server_group_update_from_form(form: dict[str, str]) -> ServerGroupUpdate:
    return ServerGroupUpdate(name=blank_none(form.get("name")))


def server_route_create_from_form(form: dict[str, str]) -> ServerRouteCreate:
    return ServerRouteCreate(
        remarks=str(form.get("remarks") or "").strip(),
        match=_list_from_text(form.get("match")),
        action=str(form.get("action") or "").strip(),
        action_value=blank_none(form.get("action_value")),
    )


def server_route_update_from_form(form: dict[str, str]) -> ServerRouteUpdate:
    return ServerRouteUpdate(
        remarks=blank_none(form.get("remarks")),
        match=_list_from_text(form.get("match")),
        action=blank_none(form.get("action")),
        action_value=blank_none(form.get("action_value")),
    )


def server_node_create_from_form(form: dict[str, str]) -> ServerV2NodeCreate:
    return ServerV2NodeCreate(
        group_id=_int_list_from_text(form.get("group_id")),
        route_id=_optional_int_list_from_text(form.get("route_id")),
        name=str(form.get("name") or "").strip(),
        parent_id=int_or_none(form.get("parent_id")),
        host=str(form.get("host") or "").strip(),
        listen_ip=str(form.get("listen_ip") or "0.0.0.0").strip(),
        port=str(form.get("port") or "").strip(),
        server_port=required_int(form.get("server_port")),
        tags=_optional_str_list_from_text(form.get("tags")),
        rate=str(form.get("rate") or "1").strip(),
        show=as_bool(form.get("show")),
        sort=int_or_none(form.get("sort")),
        protocol=str(form.get("protocol") or "").strip(),
        tls=required_int(form.get("tls")),
        tls_settings=_json_object_from_text(form.get("tls_settings")),
        flow=blank_none(form.get("flow")),
        network=str(form.get("network") or "").strip(),
        network_settings=_json_object_from_text(form.get("network_settings")),
        encryption=blank_none(form.get("encryption")),
        encryption_settings=_json_object_from_text(form.get("encryption_settings")),
        disable_sni=as_bool(form.get("disable_sni")),
        udp_relay_mode=blank_none(form.get("udp_relay_mode")),
        zero_rtt_handshake=as_bool(form.get("zero_rtt_handshake")),
        congestion_control=blank_none(form.get("congestion_control")),
        cipher=blank_none(form.get("cipher")),
        up_mbps=int_or_none(form.get("up_mbps")) or 0,
        down_mbps=int_or_none(form.get("down_mbps")) or 0,
        obfs=blank_none(form.get("obfs")),
        obfs_password=blank_none(form.get("obfs_password")),
        padding_scheme=_optional_str_list_from_text(form.get("padding_scheme")),
    )


def server_node_update_from_form(form: dict[str, str]) -> ServerV2NodeUpdate:
    return ServerV2NodeUpdate(
        group_id=_optional_int_list_from_text(form.get("group_id")),
        route_id=_optional_int_list_from_text(form.get("route_id")),
        name=blank_none(form.get("name")),
        parent_id=int_or_none(form.get("parent_id")),
        host=blank_none(form.get("host")),
        listen_ip=blank_none(form.get("listen_ip")),
        port=blank_none(form.get("port")),
        server_port=int_or_none(form.get("server_port")),
        tags=_optional_str_list_from_text(form.get("tags")),
        rate=blank_none(form.get("rate")),
        show=as_bool(form.get("show")),
        sort=int_or_none(form.get("sort")),
        protocol=blank_none(form.get("protocol")),
        tls=int_or_none(form.get("tls")),
        tls_settings=_json_object_from_text(form.get("tls_settings")),
        flow=blank_none(form.get("flow")),
        network=blank_none(form.get("network")),
        network_settings=_json_object_from_text(form.get("network_settings")),
        encryption=blank_none(form.get("encryption")),
        encryption_settings=_json_object_from_text(form.get("encryption_settings")),
        disable_sni=as_bool(form.get("disable_sni")),
        udp_relay_mode=blank_none(form.get("udp_relay_mode")),
        zero_rtt_handshake=as_bool(form.get("zero_rtt_handshake")),
        congestion_control=blank_none(form.get("congestion_control")),
        cipher=blank_none(form.get("cipher")),
        up_mbps=int_or_none(form.get("up_mbps")),
        down_mbps=int_or_none(form.get("down_mbps")),
        obfs=blank_none(form.get("obfs")),
        obfs_password=blank_none(form.get("obfs_password")),
        padding_scheme=_optional_str_list_from_text(form.get("padding_scheme")),
    )


def mail_send_from_form(form: dict[str, str]) -> MailSend:
    return MailSend(
        email=str(form.get("email") or "").strip(),
        subject=str(form.get("subject") or "").strip(),
        template_name=str(form.get("template_name") or "").strip(),
        template_value=_json_object_from_text(form.get("template_value")) or {},
    )


def _coerce_typed_value(value: str, type_hint: str) -> str | int | bool | dict | list:
    if type_hint == "int":
        return int(value or 0)
    if type_hint == "bool":
        return as_bool(value)
    if type_hint == "json":
        return _json_from_text(value)
    return value


def _json_from_text(value: str | None) -> Any:
    value = (value or "").strip()
    if not value:
        return []
    try:
        return orjson.loads(value)
    except orjson.JSONDecodeError as exc:
        raise ValueError("JSON 格式不正确") from exc


def _json_object_from_text(value: str | None) -> dict[str, Any] | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = orjson.loads(value)
    except orjson.JSONDecodeError as exc:
        raise ValueError("JSON 对象格式不正确") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON 必须是对象")
    return parsed


def _list_from_text(value: str | None) -> list[str] | None:
    items = _str_list(value)
    return items or None


def _optional_str_list_from_text(value: str | None) -> list[str] | None:
    items = _str_list(value)
    return items or None


def _int_list_from_text(value: str | None) -> list[int]:
    items = _optional_int_list_from_text(value)
    if not items:
        raise ValueError("分组 ID 不能为空")
    return items


def _optional_int_list_from_text(value: str | None) -> list[int] | None:
    raw_items = _str_list(value)
    if not raw_items:
        return None
    result: list[int] = []
    for item in raw_items:
        try:
            result.append(int(item))
        except ValueError as exc:
            raise ValueError("ID 列表必须是数字") from exc
    return result


def _str_list(value: str | None) -> list[str]:
    value = (value or "").strip()
    if not value:
        return []
    if value.startswith("["):
        try:
            parsed = orjson.loads(value)
        except orjson.JSONDecodeError as exc:
            raise ValueError("列表 JSON 格式不正确") from exc
        if not isinstance(parsed, list):
            raise ValueError("列表 JSON 必须是数组")
        return [str(item).strip() for item in parsed if str(item).strip()]
    parts: list[str] = []
    for line in value.replace(",", "\n").splitlines():
        item = line.strip()
        if item:
            parts.append(item)
    return parts
