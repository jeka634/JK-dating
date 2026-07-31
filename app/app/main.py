import asyncio, sys, json, urllib.request

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from aiogram_tonconnect.handlers import AiogramTonConnectHandlers
from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware
from aiogram_tonconnect.tonconnect.storage import ATCRedisStorage
from aiogram_tonconnect.utils.qrcode import QRUrlProvider
from tonutils.tonconnect import TonConnect

from app.config.settings import settings
from app.handlers import router as main_router
from app.middlewares import BlockedUserMiddleware, DatabaseMiddleware, UserMiddleware
from app.middlewares.session import SessionMiddleware
from app.utils.logging import get_logger, setup_logging
from app.utils.redis_cache import redis_cache

logger = get_logger(__name__)

MANIFEST_URL = "https://raw.githubusercontent.com/NicktoZz/pyton/refs/heads/main/tonconnect-manifest.json"


async def create_dispatcher() -> Dispatcher:
    await redis_cache.connect()
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # TON Connect Middleware
    tonconnect = TonConnect(
        manifest_url=MANIFEST_URL,
        storage=ATCRedisStorage(storage.redis),
    )
    dp.update.middleware.register(
        AiogramTonConnectMiddleware(
            tonconnect=tonconnect,
            qrcode_provider=QRUrlProvider(),
        )
    )
    AiogramTonConnectHandlers().register(dp)

    # Existing middlewares
    dp.update.middleware(SessionMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())
    dp.update.middleware(BlockedUserMiddleware())

    dp.include_router(main_router)
    return dp


async def on_startup(bot: Bot) -> None:
    logger.info("bot_started", mode=settings.bot_mode)
    if settings.bot_mode == "webhook" and settings.webhook_url:
        webhook_url = f"{settings.webhook_url}{settings.webhook_path}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret or None,
            drop_pending_updates=True,
        )
        logger.info("webhook_set", url=webhook_url)


async def on_shutdown(bot: Bot) -> None:
    if settings.bot_mode == "webhook":
        await bot.delete_webhook()
    await redis_cache.disconnect()
    logger.info("bot_stopped")


async def run_polling() -> None:
    setup_logging(settings.log_level)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = await create_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
