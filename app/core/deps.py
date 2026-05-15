"""统一依赖注入容器。

依赖链：
    DB:    get_db → get_user_repository → get_user_service
    Cache: get_cache → 注入 PostgreSQL UNLOGGED runtime cache
    Queue: get_queue → 直接注入 PostgreSQL 队列客户端（入队）
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RuntimeCache, get_cache
from app.core.database import get_db
from app.core.exceptions import AppException, UnauthorizedException
from app.core.queue import get_queue
from app.models.user.dto import UserRead
from app.repositories.knowledge import KnowledgeRepository
from app.repositories.commission_log import CommissionLogRepository
from app.repositories.coupon import CouponRepository
from app.repositories.failed_job import FailedJobRepository
from app.repositories.giftcard import GiftcardRepository
from app.repositories.giftcard_redemption import GiftcardRedemptionRepository
from app.repositories.invite_code import InviteCodeRepository
from app.repositories.log_event import LogEventRepository
from app.repositories.notice import NoticeRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.plan import PlanRepository
from app.repositories.server_group import ServerGroupRepository
from app.repositories.server_route import ServerRouteRepository
from app.repositories.server_v2node import ServerV2NodeRepository
from app.repositories.setting import SettingRepository
from app.repositories.ticket import TicketRepository
from app.repositories.ticket_message import TicketMessageRepository
from app.repositories.user import UserRepository
from app.services.admin_tools import FailedJobService, LogService
from app.services.auth import AuthService
from app.services.commission import InviteService
from app.services.coupon import CouponService
from app.services.giftcard import GiftcardService
from app.services.knowledge import KnowledgeService
from app.services.mail import MailService
from app.services.notice import NoticeService
from app.services.order import OrderService
from app.services.payment import PaymentService
from app.services.plan import PlanService
from app.services.server import ServerService
from app.services.server_admin import ServerAdminService
from app.services.setting import SettingService
from app.services.stat import StatService
from app.services.system import SystemService
from app.services.subscribe import SubscribeService
from app.services.telegram import TelegramService
from app.services.ticket import TicketService
from app.services.theme import ThemeService
from app.services.user import UserService

# ---- DB ----
DbDep = Depends(get_db)

# ---- Runtime cache ----
CacheDep = Depends(get_cache)

# ---- Queue ----
QueueDep = Depends(get_queue)


# ---- Auth ----
_bearer_scheme = HTTPBearer(auto_error=False)


# ---- Setting ----
def get_setting_repository(db: AsyncSession = DbDep) -> SettingRepository:
    return SettingRepository(db)


def get_setting_service(
    repo: SettingRepository = Depends(get_setting_repository),
    cache: RuntimeCache = CacheDep,
) -> SettingService:
    return SettingService(repo, cache)


# ---- Plan ----
def get_plan_repository(db: AsyncSession = DbDep) -> PlanRepository:
    return PlanRepository(db)


# ---- User ----
def get_user_repository(db: AsyncSession = DbDep) -> UserRepository:
    return UserRepository(db)


def get_invite_code_repository(db: AsyncSession = DbDep) -> InviteCodeRepository:
    return InviteCodeRepository(db)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    plan_repo: PlanRepository = Depends(get_plan_repository),
) -> UserService:
    return UserService(repo, plan_repo)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
    setting_service: SettingService = Depends(get_setting_service),
    invite_repo: InviteCodeRepository = Depends(get_invite_code_repository),
    cache: RuntimeCache = CacheDep,
) -> AuthService:
    return AuthService(repo, setting_service, invite_repo, cache)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException()
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_bearer_token),
    service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await service.get_current_user(token)


async def get_current_admin(
    token: str = Depends(get_bearer_token),
    service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await service.require_admin(token)


async def get_current_staff(
    token: str = Depends(get_bearer_token),
    service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await service.require_staff(token)


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> UserRead | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        return await service.get_current_user(credentials.credentials)
    except AppException:
        return None


# ---- Notice ----
def get_notice_repository(db: AsyncSession = DbDep) -> NoticeRepository:
    return NoticeRepository(db)


def get_notice_service(
    repo: NoticeRepository = Depends(get_notice_repository),
) -> NoticeService:
    return NoticeService(repo)


# ---- Knowledge ----
def get_knowledge_repository(db: AsyncSession = DbDep) -> KnowledgeRepository:
    return KnowledgeRepository(db)


def get_knowledge_service(
    repo: KnowledgeRepository = Depends(get_knowledge_repository),
) -> KnowledgeService:
    return KnowledgeService(repo)


def get_plan_service(
    repo: PlanRepository = Depends(get_plan_repository),
) -> PlanService:
    return PlanService(repo)


# ---- Order ----
def get_order_repository(db: AsyncSession = DbDep) -> OrderRepository:
    return OrderRepository(db)


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    setting_service: SettingService = Depends(get_setting_service),
    db: AsyncSession = DbDep,
) -> OrderService:
    return OrderService(db, setting_service)


# ---- Payment ----
def get_payment_repository(db: AsyncSession = DbDep) -> PaymentRepository:
    return PaymentRepository(db)


def get_payment_service(
    repo: PaymentRepository = Depends(get_payment_repository),
) -> PaymentService:
    return PaymentService(repo)


# ---- Coupon ----
def get_coupon_repository(db: AsyncSession = DbDep) -> CouponRepository:
    return CouponRepository(db)


def get_coupon_service(
    repo: CouponRepository = Depends(get_coupon_repository),
) -> CouponService:
    return CouponService(repo)


# ---- Giftcard ----
def get_giftcard_repository(db: AsyncSession = DbDep) -> GiftcardRepository:
    return GiftcardRepository(db)


def get_giftcard_redemption_repository(db: AsyncSession = DbDep) -> GiftcardRedemptionRepository:
    return GiftcardRedemptionRepository(db)


def get_giftcard_service(
    repo: GiftcardRepository = Depends(get_giftcard_repository),
    redemption_repo: GiftcardRedemptionRepository = Depends(get_giftcard_redemption_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    plan_repo: PlanRepository = Depends(get_plan_repository),
) -> GiftcardService:
    return GiftcardService(repo, redemption_repo, user_repo, plan_repo)


# ---- Ticket ----
def get_ticket_repository(db: AsyncSession = DbDep) -> TicketRepository:
    return TicketRepository(db)


def get_ticket_message_repository(db: AsyncSession = DbDep) -> TicketMessageRepository:
    return TicketMessageRepository(db)


def get_ticket_service(
    ticket_repo: TicketRepository = Depends(get_ticket_repository),
    message_repo: TicketMessageRepository = Depends(get_ticket_message_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    setting_service: SettingService = Depends(get_setting_service),
) -> TicketService:
    return TicketService(ticket_repo, message_repo, user_repo, order_repo, setting_service)


# ---- Invite / Commission ----
def get_commission_log_repository(db: AsyncSession = DbDep) -> CommissionLogRepository:
    return CommissionLogRepository(db)


def get_invite_service(
    invite_repo: InviteCodeRepository = Depends(get_invite_code_repository),
    commission_repo: CommissionLogRepository = Depends(get_commission_log_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    setting_service: SettingService = Depends(get_setting_service),
    db: AsyncSession = DbDep,
) -> InviteService:
    return InviteService(db, invite_repo, commission_repo, user_repo, order_repo, setting_service)


def get_log_repository(db: AsyncSession = DbDep) -> LogEventRepository:
    return LogEventRepository(db)


def get_mail_service(
    repo: LogEventRepository = Depends(get_log_repository),
    setting_service: SettingService = Depends(get_setting_service),
) -> MailService:
    return MailService(repo, setting_service)


def get_log_service(repo: LogEventRepository = Depends(get_log_repository)) -> LogService:
    return LogService(repo)


def get_failed_job_repository(db: AsyncSession = DbDep) -> FailedJobRepository:
    return FailedJobRepository(db)


def get_failed_job_service(
    repo: FailedJobRepository = Depends(get_failed_job_repository),
) -> FailedJobService:
    return FailedJobService(repo)


# ---- V2Node Server ----
def get_server_v2node_repository(db: AsyncSession = DbDep) -> ServerV2NodeRepository:
    return ServerV2NodeRepository(db)


def get_server_group_repository(db: AsyncSession = DbDep) -> ServerGroupRepository:
    return ServerGroupRepository(db)


def get_server_route_repository(db: AsyncSession = DbDep) -> ServerRouteRepository:
    return ServerRouteRepository(db)


def get_server_service(
    node_repo: ServerV2NodeRepository = Depends(get_server_v2node_repository),
    route_repo: ServerRouteRepository = Depends(get_server_route_repository),
    setting_service: SettingService = Depends(get_setting_service),
    user_repo: UserRepository = Depends(get_user_repository),
    cache: RuntimeCache = CacheDep,
    db: AsyncSession = DbDep,
) -> ServerService:
    return ServerService(node_repo, route_repo, setting_service, user_repo, cache, db)


def get_server_admin_service(
    group_repo: ServerGroupRepository = Depends(get_server_group_repository),
    route_repo: ServerRouteRepository = Depends(get_server_route_repository),
    node_repo: ServerV2NodeRepository = Depends(get_server_v2node_repository),
    db: AsyncSession = DbDep,
) -> ServerAdminService:
    return ServerAdminService(db, group_repo, route_repo, node_repo)


# ---- Subscribe ----
def get_subscribe_service(
    user_repo: UserRepository = Depends(get_user_repository),
    plan_repo: PlanRepository = Depends(get_plan_repository),
    node_repo: ServerV2NodeRepository = Depends(get_server_v2node_repository),
    setting_service: SettingService = Depends(get_setting_service),
    cache: RuntimeCache = CacheDep,
) -> SubscribeService:
    return SubscribeService(user_repo, plan_repo, node_repo, setting_service, cache)


# ---- Stats / System ----
def get_stat_service(db: AsyncSession = DbDep) -> StatService:
    return StatService(db)


def get_system_service(db: AsyncSession = DbDep) -> SystemService:
    return SystemService(db)


def get_theme_service(setting_service: SettingService = Depends(get_setting_service)) -> ThemeService:
    return ThemeService(setting_service)


def get_telegram_service(
    db: AsyncSession = DbDep,
    cache: RuntimeCache = CacheDep,
    setting_service: SettingService = Depends(get_setting_service),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TelegramService:
    return TelegramService(db, cache, setting_service, ticket_service)
