"""工单 Service。"""

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.ticket.dto import TicketCreate, TicketPublic, TicketRead, TicketReply, TicketWithdraw
from app.models.ticket.entity import Ticket
from app.models.ticket_message.dto import TicketMessagePublic
from app.models.ticket_message.entity import TicketMessage
from app.repositories.order import OrderRepository
from app.repositories.ticket import TicketRepository
from app.repositories.ticket_message import TicketMessageRepository
from app.repositories.user import UserRepository
from app.schemas.response import PaginatedData
from app.services.setting import SettingService


class TicketService:
    """工单业务逻辑。"""

    def __init__(
        self,
        ticket_repo: TicketRepository,
        message_repo: TicketMessageRepository,
        user_repo: UserRepository,
        order_repo: OrderRepository,
        setting_service: SettingService,
    ):
        self.ticket_repo = ticket_repo
        self.message_repo = message_repo
        self.user_repo = user_repo
        self.order_repo = order_repo
        self.setting_service = setting_service

    async def list_user_tickets(self, user_id: int, offset: int = 0, limit: int = 50) -> list[TicketPublic]:
        items = await self.ticket_repo.list_by_user(user_id, offset, limit)
        return [_to_public(item) for item in items]

    async def get_user_ticket(self, user_id: int, ticket_id: int) -> dict:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None or ticket.user_id != user_id:
            raise NotFoundException("工单不存在")
        return await self._ticket_detail(ticket, viewer_user_id=user_id, staff_view=False)

    async def create_ticket(self, user_id: int, data: TicketCreate) -> dict:
        if not data.subject.strip():
            raise BadRequestException("工单主题不能为空")
        if not data.message.strip():
            raise BadRequestException("工单内容不能为空")
        if await self.ticket_repo.count_open_by_user(user_id) > 0:
            raise BadRequestException("您还有未关闭的工单")
        ticket_status = await self.setting_service.get_int("ticket_status", 0)
        if ticket_status == 1 and not await self.order_repo.has_paid_order(user_id):
            raise BadRequestException("请先购买套餐")
        if ticket_status == 2:
            raise BadRequestException("当前不允许发起工单")

        ticket = Ticket(user_id=user_id, subject=data.subject.strip(), level=data.level, status=0, reply_status=0)
        ticket = await self.ticket_repo.create(ticket)
        await self.message_repo.create(
            TicketMessage(user_id=user_id, ticket_id=ticket.id, message=data.message.strip())  # type: ignore[arg-type]
        )
        return await self._ticket_detail(ticket, viewer_user_id=user_id, staff_view=False)

    async def reply_user_ticket(self, user_id: int, ticket_id: int, data: TicketReply) -> dict:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None or ticket.user_id != user_id:
            raise NotFoundException("工单不存在")
        if ticket.status != 0:
            raise BadRequestException("工单已关闭，不能回复")
        if not data.message.strip():
            raise BadRequestException("回复内容不能为空")
        last_message = await self.message_repo.get_last_by_ticket(ticket_id)
        if last_message is not None and last_message.user_id == user_id:
            raise BadRequestException("请等待客服回复")
        await self._reply(ticket, user_id, data.message.strip())
        return await self._ticket_detail(ticket, viewer_user_id=user_id, staff_view=False)

    async def close_user_ticket(self, user_id: int, ticket_id: int) -> bool:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None or ticket.user_id != user_id:
            raise NotFoundException("工单不存在")
        ticket.status = 1
        await self.ticket_repo.update(ticket)
        return True

    async def create_withdraw_ticket(self, user_id: int, data: TicketWithdraw) -> dict:
        if await self.setting_service.get_int("withdraw_close_enable", 0):
            raise BadRequestException("当前不支持佣金提现")
        methods = await self.setting_service.get_json("commission_withdraw_method", ["alipay", "usdt", "bank"])
        if data.withdraw_method not in methods:
            raise BadRequestException("不支持的提现方式")
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("用户不存在")
        limit_yuan = await self.setting_service.get_int("commission_withdraw_limit", 100)
        if user.commission_balance < limit_yuan * 100:
            raise BadRequestException(f"当前最低提现佣金为 {limit_yuan}")
        subject = "佣金提现申请"
        message = f"提现方式：{data.withdraw_method}\n提现账号：{data.withdraw_account}"
        return await self.create_ticket(user_id, TicketCreate(subject=subject, level=2, message=message))

    async def list_admin_tickets(
        self,
        page: int,
        size: int,
        *,
        status: int | None = None,
        reply_status: int | None = None,
        email: str | None = None,
    ) -> PaginatedData[TicketPublic]:
        offset = (page - 1) * size
        items = await self.ticket_repo.list_all(
            offset,
            size,
            status=status,
            reply_status=reply_status,
            email=email,
        )
        total = await self.ticket_repo.count_all(status=status, reply_status=reply_status, email=email)
        return PaginatedData(items=[_to_public(item) for item in items], total=total, page=page, size=size)

    async def get_admin_ticket(self, ticket_id: int) -> dict:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundException("工单不存在")
        return await self._ticket_detail(ticket, viewer_user_id=None, staff_view=True)

    async def reply_admin_ticket(self, admin_user_id: int, ticket_id: int, data: TicketReply) -> dict:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundException("工单不存在")
        if not data.message.strip():
            raise BadRequestException("回复内容不能为空")
        ticket.status = 0
        await self._reply(ticket, admin_user_id, data.message.strip())
        return await self._ticket_detail(ticket, viewer_user_id=admin_user_id, staff_view=True)

    async def close_admin_ticket(self, ticket_id: int) -> bool:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundException("工单不存在")
        ticket.status = 1
        await self.ticket_repo.update(ticket)
        return True

    async def _reply(self, ticket: Ticket, user_id: int, message: str) -> TicketMessage:
        ticket_message = await self.message_repo.create(
            TicketMessage(user_id=user_id, ticket_id=ticket.id, message=message)  # type: ignore[arg-type]
        )
        ticket.reply_status = 0 if user_id == ticket.user_id else 1
        await self.ticket_repo.update(ticket)
        return ticket_message

    async def _ticket_detail(
        self,
        ticket: Ticket,
        *,
        viewer_user_id: int | None,
        staff_view: bool,
    ) -> dict:
        messages = await self.message_repo.list_by_ticket(ticket.id)  # type: ignore[arg-type]
        return {
            "ticket": _to_read(ticket),
            "messages": [
                TicketMessagePublic(
                    id=item.id,  # type: ignore[arg-type]
                    user_id=item.user_id,
                    ticket_id=item.ticket_id,
                    message=item.message,
                    is_me=(item.user_id != ticket.user_id if staff_view else item.user_id == viewer_user_id),
                    created_at=item.created_at,
                )
                for item in messages
            ],
        }


def _to_public(ticket: Ticket) -> TicketPublic:
    return TicketPublic.model_validate(ticket, from_attributes=True)


def _to_read(ticket: Ticket) -> TicketRead:
    return TicketRead.model_validate(ticket, from_attributes=True)
