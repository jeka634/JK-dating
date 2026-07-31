"""JK Dating Admin Panel - Telegram bot commands for administrators."""

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.complaint import ComplaintRepository
from app.database.repositories.payment import PaymentRepository
from app.database.repositories.user import UserRepository
from app.filters import IsAdminFilter

admin_router = Router(name="admin")
admin_router.message.filter(IsAdminFilter())


@admin_router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    payment_repo = PaymentRepository(session)
    complaint_repo = ComplaintRepository(session)

    total_users = await user_repo.count_all()
    premium_users = await user_repo.count_premium()
    total_payments = await payment_repo.count_completed()
    revenue = await payment_repo.total_revenue()
    pending = await complaint_repo.count_pending()

    text = (
        f"📊 <b>JK Dating Admin Panel</b>\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"⭐ Premium: {premium_users}\n"
        f"💳 Платежей: {total_payments}\n"
        f"💰 Доход: {revenue} ⭐\n"
        f"⛔ Жалоб: {pending}\n\n"
        f"API: /admin/* endpoints\n"
        f"Команды:\n"
        f"/users - список пользователей\n"
        f"/complaints - жалобы\n"
        f"/block ID - блокировка\n"
        f"/unblock ID - разблокировка\n"
        f"/delete ID - удаление"
    )
    await message.answer(text)


@admin_router.message(Command("users"))
async def admin_users_list(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    users = await user_repo.get_all_paginated(0, 20)
    if not users:
        await message.answer("Нет пользователей.")
        return

    lines = ["👥 <b>Последние пользователи:</b>\n"]
    for user in users:
        status = "🚫" if user.is_blocked else "✅"
        premium = "⭐" if user.is_premium else ""
        lines.append(
            f"{status} ID:{user.id} TG:{user.telegram_id} "
            f"{user.name or 'N/A'} {premium}"
        )
    await message.answer("\n".join(lines))


@admin_router.message(Command("complaints"))
async def admin_complaints_list(message: Message, session: AsyncSession) -> None:
    complaint_repo = ComplaintRepository(session)
    complaints = await complaint_repo.get_pending(0, 10)
    if not complaints:
        await message.answer("Нет активных жалоб.")
        return

    lines = ["⛔ <b>Жалобы:</b>\n"]
    for c in complaints:
        lines.append(
            f"#{c.id} от user:{c.reporter_id} на user:{c.reported_user_id}\n"
            f"Причина: {c.reason[:100]}"
        )
    await message.answer("\n".join(lines))


@admin_router.message(Command("block"))
async def admin_block(message: Message, session: AsyncSession) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /block USER_ID")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("Неверный ID.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.set_blocked(user_id, True)
    if user:
        await message.answer(f"✅ Пользователь {user_id} заблокирован.")
    else:
        await message.answer("❌ Пользователь не найден.")


@admin_router.message(Command("unblock"))
async def admin_unblock(message: Message, session: AsyncSession) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /unblock USER_ID")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("Неверный ID.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.set_blocked(user_id, False)
    if user:
        await message.answer(f"✅ Пользователь {user_id} разблокирован.")
    else:
        await message.answer("❌ Пользователь не найден.")


@admin_router.message(Command("delete"))
async def admin_delete(message: Message, session: AsyncSession) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /delete USER_ID")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("Неверный ID.")
        return

    user_repo = UserRepository(session)
    success = await user_repo.delete_user(user_id)
    if success:
        await message.answer(f"✅ Пользователь {user_id} удалён.")
    else:
        await message.answer("❌ Пользователь не найден.")
