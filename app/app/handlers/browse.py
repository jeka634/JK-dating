from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config.settings import settings
from app.database.models import User
from app.keyboards import browse_keyboard, main_menu_keyboard
from app.services import BrowseService, LikeService, NotificationService
from app.states import ComplaintStates
from app.utils.texts import get_text
from aiogram.fsm.context import FSMContext

router = Router(name="browse")

BROWSE_BUTTONS_RU = {"❤️ Смотреть анкеты"}
BROWSE_BUTTONS_EN = {"❤️ Browse profiles"}


@router.message(F.text.in_(BROWSE_BUTTONS_RU | BROWSE_BUTTONS_EN))
async def browse_profiles(message: Message, db_user: User, session: object) -> None:
    if not db_user.is_registered:
        await message.answer(get_text("not_registered", db_user.language))
        return

    from sqlalchemy.ext.asyncio import AsyncSession

    browse_service = BrowseService(session)
    profile = await browse_service.get_next_profile(db_user)

    if not profile:
        await message.answer(
            get_text("browse_no_profiles", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
        return

    notification = NotificationService(message.bot)
    await notification.send_profile(
        message.chat.id,
        profile,
        db_user.language,
        reply_markup=browse_keyboard(db_user.language),
    )


@router.callback_query(F.data == "browse:like")
async def browse_like(
    callback: CallbackQuery, db_user: User, session: object
) -> None:
    from app.utils.redis_cache import redis_cache
    from sqlalchemy.ext.asyncio import AsyncSession

    profile_id = await redis_cache.get_current_profile(db_user.id)
    if not profile_id:
        await callback.answer()
        return

    like_service = LikeService(session)
    can, reason_key = await like_service.can_like(db_user)
    if not can:
        await callback.answer(
            get_text(
                reason_key or "like_limit",
                db_user.language,
                limit=settings.new_user_likes if reason_key == "new_user_like_limit" else settings.free_daily_likes,
                hours=settings.new_user_limit_hours,
            ),
            show_alert=True,
        )
        return

    success, matched_user = await like_service.send_like(db_user, profile_id)
    if not success:
        await callback.answer()
        return

    if matched_user:
        notification = NotificationService(callback.bot)
        await notification.notify_match(db_user, matched_user)
        await callback.answer(
            get_text(
                "mutual_like",
                db_user.language,
                name=matched_user.name,
                age=matched_user.age or "?",
                city=matched_user.city or "?",
                username=matched_user.username or f"id{matched_user.telegram_id}",
            ),
            show_alert=True,
        )
    else:
        await callback.answer(get_text("like_sent", db_user.language))

    browse_service = BrowseService(session)
    profile = await browse_service.get_next_profile(db_user)
    if profile:
        notification = NotificationService(callback.bot)
        await notification.send_profile(
            callback.message.chat.id,
            profile,
            db_user.language,
            reply_markup=browse_keyboard(db_user.language),
        )
    else:
        await callback.message.answer(
            get_text("browse_no_profiles", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )


@router.callback_query(F.data == "browse:skip")
async def browse_skip(
    callback: CallbackQuery, db_user: User, session: object
) -> None:
    browse_service = BrowseService(session)
    await browse_service.skip_profile(db_user)
    profile = await browse_service.get_next_profile(db_user)

    if profile:
        notification = NotificationService(callback.bot)
        await notification.send_profile(
            callback.message.chat.id,
            profile,
            db_user.language,
            reply_markup=browse_keyboard(db_user.language),
        )
    else:
        await callback.message.answer(
            get_text("browse_no_profiles", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
    await callback.answer()


@router.callback_query(F.data == "browse:report")
async def browse_report(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await callback.message.answer(
        get_text("enter_complaint_reason", db_user.language)
    )
    await state.set_state(ComplaintStates.reason)
    await callback.answer()


@router.message(ComplaintStates.reason, F.text)
async def process_complaint(
    message: Message, db_user: User, session: object, state: FSMContext
) -> None:
    from app.services import ComplaintService
    from app.utils.redis_cache import redis_cache

    profile_id = await redis_cache.get_current_profile(db_user.id)
    if not profile_id:
        await state.clear()
        return

    complaint_service = ComplaintService(session)
    await complaint_service.file_complaint(db_user.id, profile_id, message.text.strip())

    # Авто-блокировка при 3+ жалобах
    from app.database.models import Complaint, ComplaintStatus
    from app.database.repositories.user import UserRepository
    from sqlalchemy import func, select

    pending_count = await session.scalar(
        select(func.count(Complaint.id)).where(
            Complaint.reported_user_id == profile_id,
            Complaint.status == ComplaintStatus.PENDING,
        )
    )
    if pending_count and pending_count >= 3:
        user_repo = UserRepository(session)
        reported_user = await user_repo.get_by_id(profile_id)
        if reported_user and not reported_user.is_blocked:
            await user_repo.set_blocked(profile_id, True)
            try:
                await message.bot.send_message(
                    reported_user.telegram_id,
                    f"🚫 Ваша анкета заблокирована — получено {pending_count} жалоб от пользователей.",
                )
            except Exception:
                pass

    await state.clear()
    await message.answer(
        get_text("complaint_sent", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )
