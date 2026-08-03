from aiogram import Router

from admin_panel import admin_router
from app.handlers import browse, premium, registration, settings, start, verify

router = Router(name="main")

router.include_router(start.router)
router.include_router(registration.router)
router.include_router(browse.router)
router.include_router(premium.router)
router.include_router(settings.router)
router.include_router(verify.router)
router.include_router(admin_router)
