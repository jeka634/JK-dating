from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models import Gender, User
from app.database.repositories.user import UserRepository
from app.keyboards import main_menu_keyboard
from app.utils.logging import get_logger
from app.utils.texts import get_text

logger = get_logger(__name__)

router = Router(name="verify")


async def _send_to_admin(message: Message, photo_file_id: str, db_user: User) -> None:
    """Пересылает селфи админу с кнопками подтверждения."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    caption = (
        f"🆔 User ID: {db_user.id}\n"
        f"👤 @{db_user.username or 'нет username'}\n"
        f"📛 {db_user.name or '?'}, {db_user.age or '?'} лет, {db_user.city or '?'}\n\n"
        f"Анкета: https://t.me/{settings.bot_username or 'JKdating_bot'}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"verify:approve:{db_user.id}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"verify:reject:{db_user.id}",
            ),
        ]
    ])
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_photo(
                admin_id,
                photo=photo_file_id,
                caption=caption,
                reply_markup=kb,
            )
            logger.info("verify_sent_to_admin", admin_id=admin_id, user_id=db_user.id)
        except Exception as e:
            logger.error("verify_admin_send_failed", admin_id=admin_id, error=str(e))


@router.message(F.photo, User)
async def handle_verification_photo(message: Message, db_user: User) -> None:
    """Неверифицированная женщина прислала фото — считаем это селфи-верификацией."""
    if not db_user.is_registered:
        return
    if db_user.gender != Gender.FEMALE:
        return
    if db_user.is_verified:
        return

    photo = message.photo[-1]
    await _send_to_admin(message, photo.file_id, db_user)
    await message.answer(
        get_text("verify_photo_sent", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )


async def _require_admin(callback: CallbackQuery) -> bool:
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return False
    return True


@router.callback_query(F.data.startswith("verify:approve:"))
async def verify_approve(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _require_admin(callback):
        return
    try:
        user_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Ошибка данных", show_alert=True)
        return

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    user.is_verified = True
    await session.commit()

    try:
        await callback.bot.send_message(
            user.telegram_id,
            get_text("verify_approved", user.language),
            reply_markup=main_menu_keyboard(user.language),
        )
    except Exception:
        pass

    await callback.answer("✅ Анкета подтверждена")
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n✅ ПОДТВЕРЖДЕНО"
        )
    except Exception:
        pass
    logger.info("verify_approved", admin_id=callback.from_user.id, user_id=user_id)


@router.callback_query(F.data.startswith("verify:reject:"))
async def verify_reject(callback: CallbackQuery, session: AsyncSession) -> None:
    if not await _require_admin(callback):
        return
    try:
        user_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Ошибка данных", show_alert=True)
        return

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    try:
        await callback.bot.send_message(
            user.telegram_id,
            get_text("verify_rejected", user.language),
            reply_markup=main_menu_keyboard(user.language),
        )
    except Exception:
        pass

    await callback.answer("❌ Отклонено")
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ ОТКЛОНЕНО"
        )
    except Exception:
        pass
    logger.info("verify_rejected", admin_id=callback.from_user.id, user_id=user_id)
