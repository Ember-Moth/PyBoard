"""失败任务 管理端控制器。"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import QueueDep, get_current_admin, get_failed_job_service
from app.core.queue import PostgresQueue
from app.core.response_utils import success
from app.schemas.response import ApiResponse
from app.services.admin_tools import FailedJobService

router = APIRouter(
    prefix="/api/v1/admin/failed-jobs",
    tags=["管理-失败任务"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=ApiResponse[list])
async def list_failed_jobs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: FailedJobService = Depends(get_failed_job_service),
):
    jobs = await service.list_jobs(offset, limit)
    return success(data=jobs)


@router.get("/{job_id}", response_model=ApiResponse[dict])
async def get_failed_job(job_id: int, service: FailedJobService = Depends(get_failed_job_service)):
    job = await service.get_job(job_id)
    return success(data=job)


@router.post("/{job_id}/retry", response_model=ApiResponse[bool])
async def retry_failed_job(
    job_id: int,
    queue: PostgresQueue = QueueDep,
    service: FailedJobService = Depends(get_failed_job_service),
):
    result = await service.retry_job(job_id, queue)
    return success(data=result)


@router.delete("/{job_id}", status_code=204)
async def delete_failed_job(job_id: int, service: FailedJobService = Depends(get_failed_job_service)):
    await service.delete_job(job_id)
