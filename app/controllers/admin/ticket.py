"""工单 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_ticket_service
from app.core.response_utils import success
from app.models.ticket.dto import TicketReply
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.ticket import TicketService

router = APIRouter(
    prefix="/api/v1/admin/tickets",
    tags=["管理-工单"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[dict])
async def list_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    status: int | None = Query(None),
    reply_status: int | None = Query(None),
    email: str | None = Query(None),
    service: TicketService = Depends(get_ticket_service),
):
    tickets = await service.list_admin_tickets(
        page,
        size,
        status=status,
        reply_status=reply_status,
        email=email,
    )
    return success(data=tickets)


@router.get("/{ticket_id}", response_model=ApiResponse[dict])
async def get_ticket(ticket_id: int, service: TicketService = Depends(get_ticket_service)):
    ticket = await service.get_admin_ticket(ticket_id)
    return success(data=ticket)


@router.post("/{ticket_id}/reply", response_model=ApiResponse[dict])
async def reply_ticket(
    ticket_id: int,
    data: TicketReply,
    current_admin: UserRead = Depends(get_current_admin),
    service: TicketService = Depends(get_ticket_service),
):
    ticket = await service.reply_admin_ticket(current_admin.id, ticket_id, data)
    return success(data=ticket)


@router.post("/{ticket_id}/close", response_model=ApiResponse[bool])
async def close_ticket(ticket_id: int, service: TicketService = Depends(get_ticket_service)):
    result = await service.close_admin_ticket(ticket_id)
    return success(data=result)
