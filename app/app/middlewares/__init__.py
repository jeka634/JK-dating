from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user import UserRepository
from app.services import PremiumService, UserService
from app.utils.texts import get_text


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data["session"]
        data["user_service"] = UserService(session)
        data["premium_service"] = PremiumService(session)
        return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        user_service: UserService = data["user_service"]
        premium_service: PremiumService = data["premium_service"]

        referral_code = None
        if hasattr(event, "text") and event.text and event.text.startswith("/start"):
            parts = event.text.split()
            if len(parts) > 1 and parts[1].startswith("ref_"):
                referral_code = parts[1].replace("ref_", "")

        user = await user_service.get_or_create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            referral_code=referral_code,
        )
        user = await premium_service.check_premium_expiry(user)

        data["db_user"] = user
        return await handler(event, data)


class BlockedUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("db_user")
        if user and user.is_blocked:
            if hasattr(event, "answer"):
                await event.answer(get_text("blocked", user.language))
            return None
        return await handler(event, data)
