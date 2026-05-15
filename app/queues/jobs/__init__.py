"""任务注册中心 —— 汇总所有 job 文件，统一导出。"""

# ruff: noqa: E402

from app.core.runtime import configure_async_runtime

ASYNC_RUNTIME = configure_async_runtime()

from app.queues.jobs.commission import calc_commission
from app.queues.jobs.mail import send_mail
from app.queues.jobs.maintenance import aggregate_yesterday_stats, check_order, cleanup_log_events, traffic_update
from app.queues.jobs.order import order_handle
from app.queues.jobs.stat import aggregate_stats
from app.queues.jobs.telegram import send_telegram
from app.queues.jobs.traffic import stat_server, stat_user, traffic_fetch

__all__ = [
    "ASYNC_RUNTIME",
    "send_mail",
    "send_telegram",
    "order_handle",
    "calc_commission",
    "aggregate_stats",
    "traffic_update",
    "check_order",
    "aggregate_yesterday_stats",
    "cleanup_log_events",
    "traffic_fetch",
    "stat_user",
    "stat_server",
]
