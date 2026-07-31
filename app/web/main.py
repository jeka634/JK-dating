from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models import AdminLog, ComplaintStatus
from app.database.repositories.complaint import ComplaintRepository
from app.database.repositories.like import LikeRepository
from app.database.repositories.match import MatchRepository
from app.database.repositories.payment import PaymentRepository
from app.database.repositories.premium import PremiumRepository
from app.database.repositories.user import UserRepository
from app.database.session import async_session_factory, get_session
from app.utils.logging import get_logger, setup_logging
from app.utils.redis_cache import redis_cache

setup_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(title="JK Dating API", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    await redis_cache.connect()
    logger.info("api_started")


@app.on_event("shutdown")
async def shutdown() -> None:
    await redis_cache.disconnect()
    logger.info("api_stopped")


async def verify_admin_key(x_admin_key: str = Header(...)) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin API key")


async def get_db_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    name: Optional[str]
    age: Optional[int]
    city: Optional[str]
    is_premium: bool
    is_blocked: bool
    is_registered: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_users: int
    premium_users: int
    total_payments: int
    completed_payments: int
    total_revenue_stars: int
    total_matches: int
    pending_complaints: int


class ComplaintResponse(BaseModel):
    id: int
    reporter_id: int
    reported_user_id: int
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogResponse(BaseModel):
    id: int
    admin_telegram_id: int
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


async def log_admin_action(
    session: AsyncSession,
    admin_id: int,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[str] = None,
) -> None:
    log_entry = AdminLog(
        admin_telegram_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    session.add(log_entry)
    await session.flush()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "jk-dating-api"}


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.types import Update

    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if settings.webhook_secret and secret != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    data = await request.json()
    update = Update.model_validate(data)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    from app.main import create_dispatcher

    dp = await create_dispatcher()
    await dp.feed_update(bot, update)
    await bot.session.close()
    return {"ok": True}


@app.get("/admin/stats", response_model=StatsResponse, dependencies=[Depends(verify_admin_key)])
async def admin_stats(session: AsyncSession = Depends(get_db_session)) -> StatsResponse:
    user_repo = UserRepository(session)
    payment_repo = PaymentRepository(session)
    match_repo = MatchRepository(session)
    complaint_repo = ComplaintRepository(session)

    return StatsResponse(
        total_users=await user_repo.count_all(),
        premium_users=await user_repo.count_premium(),
        total_payments=await payment_repo.count_all(),
        completed_payments=await payment_repo.count_completed(),
        total_revenue_stars=await payment_repo.total_revenue(),
        total_matches=await match_repo.count_all(),
        pending_complaints=await complaint_repo.count_pending(),
    )


@app.get("/admin/users", response_model=List[UserResponse], dependencies=[Depends(verify_admin_key)])
async def admin_users(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> List[UserResponse]:
    user_repo = UserRepository(session)
    users = await user_repo.get_all_paginated(offset, limit)
    return [UserResponse.model_validate(u) for u in users]


@app.delete("/admin/users/{user_id}", dependencies=[Depends(verify_admin_key)])
async def admin_delete_user(
    user_id: int,
    x_admin_telegram_id: int = Header(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    user_repo = UserRepository(session)
    success = await user_repo.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await log_admin_action(session, x_admin_telegram_id, "delete_user", "user", user_id)
    return {"ok": True, "deleted_user_id": user_id}


@app.post("/admin/users/{user_id}/block", dependencies=[Depends(verify_admin_key)])
async def admin_block_user(
    user_id: int,
    x_admin_telegram_id: int = Header(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    user_repo = UserRepository(session)
    user = await user_repo.set_blocked(user_id, True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_admin_action(session, x_admin_telegram_id, "block_user", "user", user_id)
    return {"ok": True, "user_id": user_id, "blocked": True}


@app.post("/admin/users/{user_id}/unblock", dependencies=[Depends(verify_admin_key)])
async def admin_unblock_user(
    user_id: int,
    x_admin_telegram_id: int = Header(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    user_repo = UserRepository(session)
    user = await user_repo.set_blocked(user_id, False)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_admin_action(session, x_admin_telegram_id, "unblock_user", "user", user_id)
    return {"ok": True, "user_id": user_id, "blocked": False}


@app.get("/admin/complaints", response_model=List[ComplaintResponse], dependencies=[Depends(verify_admin_key)])
async def admin_complaints(
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> List[ComplaintResponse]:
    complaint_repo = ComplaintRepository(session)
    if status == "pending":
        complaints = await complaint_repo.get_pending(offset, limit)
    else:
        complaints = await complaint_repo.get_all(offset, limit)
    return [ComplaintResponse.model_validate(c) for c in complaints]


@app.post("/admin/complaints/{complaint_id}/resolve", dependencies=[Depends(verify_admin_key)])
async def admin_resolve_complaint(
    complaint_id: int,
    status: str = "resolved",
    admin_note: Optional[str] = None,
    x_admin_telegram_id: int = Header(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    complaint_repo = ComplaintRepository(session)
    complaint = await complaint_repo.get_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    status_map = {
        "resolved": ComplaintStatus.RESOLVED,
        "rejected": ComplaintStatus.REJECTED,
        "reviewed": ComplaintStatus.REVIEWED,
    }
    new_status = status_map.get(status, ComplaintStatus.RESOLVED)
    await complaint_repo.resolve(complaint, new_status, admin_note)
    await log_admin_action(
        session,
        x_admin_telegram_id,
        "resolve_complaint",
        "complaint",
        complaint_id,
        admin_note,
    )
    return {"ok": True, "complaint_id": complaint_id, "status": new_status.value}


@app.get("/admin/payments", dependencies=[Depends(verify_admin_key)])
async def admin_payments(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> list:
    payment_repo = PaymentRepository(session)
    payments = await payment_repo.get_recent(offset, limit)
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "amount": p.amount,
            "currency": p.currency,
            "method": p.method.value,
            "status": p.status.value,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]


@app.get("/admin/logs", response_model=List[AdminLogResponse], dependencies=[Depends(verify_admin_key)])
async def admin_logs(
    offset: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
) -> List[AdminLogResponse]:
    from sqlalchemy import select

    from app.database.models import AdminLog as AdminLogModel

    result = await session.execute(
        select(AdminLogModel)
        .order_by(AdminLogModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = result.scalars().all()
    return [AdminLogResponse.model_validate(log) for log in logs]
