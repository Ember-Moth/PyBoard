from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.controllers import account, admin_ui, auth, comm, coupon, giftcard, invite, knowledge, notice, order, payment, plan, server, staff, subscribe, ticket, user
from app.controllers.admin import coupon as admin_coupon
from app.controllers.admin import failed_job as admin_failed_job
from app.controllers.admin import giftcard as admin_giftcard
from app.controllers.admin import invite as admin_invite
from app.controllers.admin import knowledge as admin_knowledge
from app.controllers.admin import log as admin_log
from app.controllers.admin import mail as admin_mail
from app.controllers.admin import notice as admin_notice
from app.controllers.admin import order as admin_order
from app.controllers.admin import payment as admin_payment
from app.controllers.admin import plan as admin_plan
from app.controllers.admin import server as admin_server
from app.controllers.admin import setting as admin_setting
from app.controllers.admin import stat as admin_stat
from app.controllers.admin import system as admin_system
from app.controllers.admin import theme as admin_theme
from app.controllers.admin import ticket as admin_ticket
from app.core.database import close_db, init_db
from app.core.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppException
from app.core.queue import close_queue
from app.core.request_logging import register_request_logging
from app.core.runtime import configure_async_runtime


ASYNC_RUNTIME = configure_async_runtime()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_queue()
    await close_db()


app = FastAPI(lifespan=lifespan)
register_request_logging(app)

app.include_router(auth.router)
app.include_router(account.router)
app.include_router(comm.guest_router)
app.include_router(comm.user_router)
app.include_router(comm.telegram_router)
app.include_router(user.router)
app.include_router(notice.router)
app.include_router(knowledge.router)
app.include_router(plan.router)
app.include_router(order.router)
app.include_router(coupon.router)
app.include_router(giftcard.router)
app.include_router(ticket.router)
app.include_router(invite.router)
app.include_router(payment.router)
app.include_router(payment.methods_router)
app.include_router(subscribe.client_router)
app.include_router(subscribe.user_router)
app.include_router(server.router)
app.include_router(server.uniproxy_router)
app.include_router(staff.router)
app.include_router(admin_notice.router)
app.include_router(admin_knowledge.router)
app.include_router(admin_plan.router)
app.include_router(admin_setting.router)
app.include_router(admin_order.router)
app.include_router(admin_payment.router)
app.include_router(admin_server.router)
app.include_router(admin_stat.router)
app.include_router(admin_system.router)
app.include_router(admin_theme.router)
app.include_router(admin_coupon.router)
app.include_router(admin_giftcard.router)
app.include_router(admin_ticket.router)
app.include_router(admin_invite.router)
app.include_router(admin_mail.router)
app.include_router(admin_log.router)
app.include_router(admin_failed_job.router)
app.include_router(admin_ui.router)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
