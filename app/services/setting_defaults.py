"""系统配置默认值。

这里是默认配置的唯一清单：
- SettingService 用它渲染分组配置。
- 迁移 seed 用它初始化 setting。
"""

from dataclasses import dataclass
from typing import Any, Literal

import orjson

SettingType = Literal["str", "int", "json"]


@dataclass(frozen=True)
class SettingDefault:
    key: str
    value: Any
    type: SettingType
    description: str
    zero_as_none: bool = False


DEFAULT_SETTING_GROUPS: dict[str, tuple[SettingDefault, ...]] = {
    "ticket": (
        SettingDefault("ticket_status", 0, "int", "工单开放策略"),
    ),
    "deposit": (
        SettingDefault("deposit_bounus", [], "json", "充值赠送规则"),
    ),
    "invite": (
        SettingDefault("invite_force", 0, "int", "注册必须填写邀请码"),
        SettingDefault("invite_commission", 10, "int", "默认返佣比例"),
        SettingDefault("invite_gen_limit", 5, "int", "每人可生成邀请码数量"),
        SettingDefault("invite_never_expire", 0, "int", "邀请码长期有效"),
        SettingDefault("commission_first_time_enable", 1, "int", "仅首单返佣"),
        SettingDefault("commission_auto_check_enable", 1, "int", "自动确认佣金"),
        SettingDefault("commission_withdraw_limit", 100, "int", "最低提现金额"),
        SettingDefault("commission_withdraw_method", ["alipay", "usdt", "bank"], "json", "可用提现方式"),
        SettingDefault("withdraw_close_enable", 0, "int", "关闭佣金提现"),
        SettingDefault("commission_distribution_enable", 0, "int", "开启多级分销"),
        SettingDefault("commission_distribution_l1", 0, "int", "一级分销比例", zero_as_none=True),
        SettingDefault("commission_distribution_l2", 0, "int", "二级分销比例", zero_as_none=True),
        SettingDefault("commission_distribution_l3", 0, "int", "三级分销比例", zero_as_none=True),
    ),
    "site": (
        SettingDefault("logo", "", "str", "站点 Logo"),
        SettingDefault("stop_register", 0, "int", "暂停新用户注册"),
        SettingDefault("app_name", "PyBoard", "str", "应用名称"),
        SettingDefault("app_description", "PyBoard panel backend.", "str", "应用简介"),
        SettingDefault("app_url", "", "str", "站点访问地址"),
        SettingDefault("subscribe_url", "", "str", "订阅地址"),
        SettingDefault("subscribe_path", "", "str", "订阅路径"),
        SettingDefault("try_out_plan_id", 0, "int", "试用套餐编号"),
        SettingDefault("try_out_hour", 1, "int", "试用时长（小时）"),
        SettingDefault("tos_url", "", "str", "服务条款地址"),
        SettingDefault("currency", "CNY", "str", "结算币种"),
        SettingDefault("currency_symbol", "¥", "str", "货币符号"),
    ),
    "subscribe": (
        SettingDefault("plan_change_enable", 1, "int", "允许用户变更套餐"),
        SettingDefault("reset_traffic_method", 0, "int", "流量重置方式"),
        SettingDefault("surplus_enable", 1, "int", "启用剩余价值折抵"),
        SettingDefault("allow_new_period", 0, "int", "允许购买新周期"),
        SettingDefault("new_order_event_id", 0, "int", "新购事件编号"),
        SettingDefault("renew_order_event_id", 0, "int", "续费事件编号"),
        SettingDefault("change_order_event_id", 0, "int", "变更套餐事件编号"),
        SettingDefault("show_info_to_server_enable", 0, "int", "向节点下发订阅信息"),
        SettingDefault("show_subscribe_method", 0, "int", "订阅展示方式"),
        SettingDefault("show_subscribe_expire", 5, "int", "订阅过期提醒天数"),
    ),
    "server": (
        SettingDefault("server_api_url", "", "str", "节点 API 地址"),
        SettingDefault("server_token", "", "str", "节点通信密钥"),
        SettingDefault("server_pull_interval", 60, "int", "节点拉取间隔（秒）"),
        SettingDefault("server_push_interval", 60, "int", "节点上报间隔（秒）"),
        SettingDefault("server_node_report_min_traffic", 0, "int", "节点上报最小流量"),
        SettingDefault("server_device_online_min_traffic", 0, "int", "设备在线最小流量"),
        SettingDefault("device_limit_mode", 0, "int", "设备限制统计方式"),
    ),
    "email": (
        SettingDefault("email_template", "default", "str", "邮件模板"),
        SettingDefault("email_host", "", "str", "SMTP 主机"),
        SettingDefault("email_port", 0, "int", "SMTP 端口"),
        SettingDefault("email_username", "", "str", "SMTP 用户名"),
        SettingDefault("email_password", "", "str", "SMTP 密码"),
        SettingDefault("email_encryption", "", "str", "SMTP 加密方式"),
        SettingDefault("email_from_address", "", "str", "发件邮箱"),
    ),
    "telegram": (
        SettingDefault("telegram_bot_enable", 0, "int", "启用 Telegram 机器人"),
        SettingDefault("telegram_bot_token", "", "str", "Telegram Bot Token"),
        SettingDefault("telegram_discuss_link", "", "str", "Telegram 讨论群链接"),
    ),
    "app": (
        SettingDefault("windows_version", "", "str", "Windows 客户端版本"),
        SettingDefault("windows_download_url", "", "str", "Windows 下载地址"),
        SettingDefault("macos_version", "", "str", "macOS 客户端版本"),
        SettingDefault("macos_download_url", "", "str", "macOS 下载地址"),
        SettingDefault("android_version", "", "str", "Android 客户端版本"),
        SettingDefault("android_download_url", "", "str", "Android 下载地址"),
    ),
    "safe": (
        SettingDefault("email_verify", 0, "int", "启用邮箱验证码"),
        SettingDefault("safe_mode_enable", 0, "int", "启用安全模式"),
        SettingDefault("email_whitelist_enable", 0, "int", "启用邮箱后缀白名单"),
        SettingDefault(
            "email_whitelist_suffix",
            ["gmail.com", "qq.com", "163.com", "outlook.com", "hotmail.com"],
            "json",
            "允许注册的邮箱后缀",
        ),
        SettingDefault("email_gmail_limit_enable", 0, "int", "限制 Gmail 别名注册"),
        SettingDefault("recaptcha_enable", 0, "int", "启用 Cloudflare Turnstile"),
        SettingDefault("recaptcha_key", "", "str", "Turnstile Secret Key"),
        SettingDefault("recaptcha_site_key", "", "str", "Turnstile Site Key"),
        SettingDefault("register_limit_by_ip_enable", 0, "int", "限制同 IP 注册"),
        SettingDefault("register_limit_count", 3, "int", "同 IP 注册次数"),
        SettingDefault("register_limit_expire", 60, "int", "注册限制周期（分钟）"),
        SettingDefault("password_limit_enable", 1, "int", "启用密码错误限制"),
        SettingDefault("password_limit_count", 5, "int", "密码错误次数"),
        SettingDefault("password_limit_expire", 60, "int", "密码限制周期（分钟）"),
    ),
}


DEFAULT_SETTINGS: tuple[SettingDefault, ...] = tuple(
    item
    for group in DEFAULT_SETTING_GROUPS.values()
    for item in group
)


def serialize_setting_value(item: SettingDefault) -> str:
    if item.type == "json":
        return orjson.dumps(item.value).decode()
    return str(item.value)
