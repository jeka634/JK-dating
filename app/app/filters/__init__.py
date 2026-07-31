from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.config.settings import settings


class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.admin_ids
