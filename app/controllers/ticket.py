"""工单 用户端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, get_ticket_service
from app.core.response_utils import created, success
from app.models.ticket.dto import TicketCreate, TicketReply, TicketWithdraw
from app.models.user.dto import UserRead
from app.schemas.response import ApiResponse
from app.services.ticket import TicketService

router = APIRouter(prefix="/api/v1/tickets", tags=["工单"])


@router.get("", response_model=ApiResponse[list])
async def list_tickets(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserRead = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    """获取当前用户工单列表。"""
    tickets = await service.list_user_tickets(current_user.id, offset, limit)
    return success(data=tickets)


@router.get("/{ticket_id}", response_model=ApiResponse[dict])
async def get_ticket(
    ticket_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    """获取当前用户工单详情。"""
    ticket = await service.get_user_ticket(current_user.id, ticket_id)
    return success(data=ticket)


@router.post("", response_model=ApiResponse[dict], status_code=201)
async def create_ticket(
    data: TicketCreate,
    current_user: UserRead = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    """创建工单。"""
    ticket = await service.create_ticket(current_user.id, data)
    return created(data=ticket)


@router.post("/{ticket_id}/reply", response_model=ApiResponse[dict])
async def reply_ticket(
    ticket_id: int,
    data: TicketReply,
    current_user: UserRead = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    """回复工单。"""
    ticket = await service.reply_user_ticket(current_user.id, ticket_id, data)
    return success(data=ticket)


@router.post("/{ticket_id}/close", response_model=ApiResponse[bool])
async def close_ticket(
    ticket_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    """关闭工单。"""
    result = await service.close_user_ticket(current_user.id, ticket_id)
    return success(data=result)


@router.post("/withdraw", response_model=ApiResponse[dict], status_code=201)
async def create_withdraw_ticket(
    data: TicketWithdraw,
    current_user: UserRead = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    """创建佣金提现工单。"""
    ticket = await service.create_withdraw_ticket(current_user.id, data)
    return created(data=ticket)
