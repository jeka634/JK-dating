"""TON Connect для JK Dating — интеграция через aiogram-tonconnect."""
import json, urllib.request, logging

from aiogram import Router, F, types
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import ConnectWalletCallbacks

from app.keyboards import main_menu_keyboard
from app.database.models import User, Language

router = Router(name="ton_wallet")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)

logger = logging.getLogger(__name__)


class TonConnectService:
    """Совместимость со старым кодом."""
    async def validate_address(self, address: str) -> bool:
        return bool(address and len(address) >= 48)

    async def get_wallet_info(self, address: str) -> dict:
        return {"address": address, "balance": "0"}


JK_TOKEN = "EQAK3lkmVshzYJeypOCtPBnE_kOJ4Nb9hwyRvQJeRDDW6HPM"


async def fetch_jk_balance(wallet_address: str) -> str | None:
    """Запрашивает баланс JK Coin через TON API."""
    try:
        url = f"https://tonapi.io/v2/accounts/{wallet_address}/jettons/{JK_TOKEN}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        balance = int(data.get("balance", 0)) / 1e9
        return f"{balance:,.0f}" if balance > 0 else "0"
    except Exception as e:
        logger.debug(f"JK balance: {e}")
        return None


@router.message(F.text.in_(["💎 Tonkeeper (TON)", "Tonkeeper (TON)", "Tonkeeper"]))
async def ton_connect_handler(message: types.Message, atc_manager: ATCManager, state: FSMContext) -> None:
    """Подключение TON кошелька через TonConnect."""

    async def after_connect():
        """Вызывается после успешного подключения."""
        address = atc_manager.user.wallet_address
        if address:
            # Сохраняем в БД
            from app.database.session import get_session
            from sqlalchemy import select
            async with get_session() as session:
                stmt = select(User).where(User.telegram_id == message.from_user.id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    user.ton_wallet_address = address
                    await session.commit()

        jk_balance = await fetch_jk_balance(address) if address else None
        lang = Language.RU
        from app.database.session import get_session
        from sqlalchemy import select
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == message.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                lang = user.language or Language.RU

        balance_line = f"\n💰 JK баланс: {jk_balance} JK" if jk_balance else ""
        await message.answer(
            f"✅ Кошелёк подключён!\n`{address[:20]}...`{balance_line}",
            reply_markup=main_menu_keyboard(lang),
        )

    callbacks = ConnectWalletCallbacks(
        after_callback=after_connect,
    )
    await atc_manager.connect_wallet(callbacks)
