"""Staff 控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import (
    get_current_staff,
    get_mail_service,
    get_notice_service,
    get_plan_service,
    get_ticket_service,
    get_user_service,
)
from app.core.response_utils import created, success
from app.models.mail.dto import MailSend
from app.models.notice.dto import NoticeCreate, NoticeUpdate
from app.models.ticket.dto import TicketReply
from app.models.user.dto import AdminUserBan, UserRead, UserUpdate
from app.schemas.response import ApiResponse
from app.services.mail import MailService
from app.services.notice import NoticeService
from app.services.plan import PlanService
from app.services.ticket import TicketService
from app.services.user import UserService

router = APIRouter(
    prefix="/api/v1/staff",
    tags=["Staff"],
    dependencies=[Depends(get_current_staff)],
)


@router.get("/tickets", response_model=ApiResponse[dict])
async def list_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    status: int | None = Query(None),
    service: TicketService = Depends(get_ticket_service),
):
    return success(data=await service.list_admin_tickets(page, size, status=status))


@router.get("/tickets/{ticket_id}", response_model=ApiResponse[dict])
async def get_ticket(ticket_id: int, service: TicketService = Depends(get_ticket_service)):
    return success(data=await service.get_admin_ticket(ticket_id))


@router.post("/tickets/{ticket_id}/reply", response_model=ApiResponse[dict])
async def reply_ticket(
    ticket_id: int,
    data: TicketReply,
    current_staff: UserRead = Depends(get_current_staff),
    service: TicketService = Depends(get_ticket_service),
):
    return success(data=await service.reply_admin_ticket(current_staff.id, ticket_id, data))


@router.post("/tickets/{ticket_id}/close", response_model=ApiResponse[bool])
async def close_ticket(ticket_id: int, service: TicketService = Depends(get_ticket_service)):
    return success(data=await service.close_admin_ticket(ticket_id))


@router.get("/users/{user_id}", response_model=ApiResponse[UserRead])
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return success(data=await service.get_user(user_id))


@router.patch("/users/{user_id}", response_model=ApiResponse[UserRead])
async def update_user(user_id: int, data: UserUpdate, service: UserService = Depends(get_user_service)):
    return success(data=await service.update_user(user_id, data))


@router.post("/users/{user_id}/ban", response_model=ApiResponse[bool])
async def ban_user(user_id: int, data: AdminUserBan, service: UserService = Depends(get_user_service)):
    return success(data=await service.admin_set_banned(user_id, data))


@router.post("/users/{user_id}/mail", response_model=ApiResponse[bool])
async def send_user_mail(user_id: int, data: MailSend, service: UserService = Depends(get_user_service), mail_service: MailService = Depends(get_mail_service)):
    user = await service.get_user(user_id)
    payload = data.model_copy(update={"email": user.email})
    return success(data=await mail_service.send(payload))


@router.get("/plans", response_model=ApiResponse[list])
async def list_plans(service: PlanService = Depends(get_plan_service)):
    return success(data=await service.list_all())


@router.get("/notices", response_model=ApiResponse[dict])
async def list_notices(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    service: NoticeService = Depends(get_notice_service),
):
    return success(data=await service.list_all(page, size))


@router.post("/notices", response_model=ApiResponse[dict], status_code=201)
async def create_notice(data: NoticeCreate, service: NoticeService = Depends(get_notice_service)):
    return created(data=await service.create(data))


@router.patch("/notices/{notice_id}", response_model=ApiResponse[dict])
async def update_notice(notice_id: int, data: NoticeUpdate, service: NoticeService = Depends(get_notice_service)):
    return success(data=await service.update(notice_id, data))


@router.delete("/notices/{notice_id}", status_code=204)
async def delete_notice(notice_id: int, service: NoticeService = Depends(get_notice_service)):
    await service.delete(notice_id)
