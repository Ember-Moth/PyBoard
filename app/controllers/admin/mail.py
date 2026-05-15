"""邮件 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin, get_mail_service
from app.core.response_utils import success
from app.models.mail.dto import MailSend
from app.schemas.response import ApiResponse
from app.services.mail import MailService

router = APIRouter(
    prefix="/api/v1/admin/mail",
    tags=["管理-邮件"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("/send", response_model=ApiResponse[bool])
async def send_mail(data: MailSend, service: MailService = Depends(get_mail_service)):
    result = await service.send(data)
    return success(data=result)


@router.get("/logs", response_model=ApiResponse[list])
async def list_mail_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: MailService = Depends(get_mail_service),
):
    logs = await service.list_logs(offset, limit)
    return success(data=logs)


@router.get("/logs/{log_id}", response_model=ApiResponse[dict])
async def get_mail_log(log_id: int, service: MailService = Depends(get_mail_service)):
    log = await service.get_log(log_id)
    return success(data=log)
