"""
Простое подключение TON кошелька.
Кнопка "💎 Tonkeeper (TON)" → показать инструкцию → принять адрес → показать баланс JK.
"""
import re, json, urllib.request, logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database.models import User, Language
from app.database.session import get_session
from app.keyboards import main_menu_keyboard
from sqlalchemy import select

router = Router(name="ton_wallet")
logger = logging.getLogger(__name__)

class TonConnectService:
    """Совместимость."""
    pass


JK_TOKEN = "EQAK3lkmVshzYJeypOCtPBnE_kOJ4Nb9hwyRvQJeRDDW6HPM"


class TonWalletStates(StatesGroup):
    waiting_address = State()


def validate_ton_address(address: str) -> bool:
    """Валидация TON адреса: EQ... или UQ... длина 48."""
    address = address.strip()
    return bool(re.match(r'^[EU][Qq][A-Za-z0-9+/=_-]{46}$', address))


async def fetch_jk_balance(wallet_address: str) -> str | None:
    """Баланс JK Coin через TON API."""
    try:
        url = f"https://tonapi.io/v2/accounts/{wallet_address}/jettons/{JK_TOKEN}"
        req = urllib.request.Request(url, headers={"User-Agent": "JK-Dating/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        balance = int(data.get("balance", 0)) / 1e9
        return f"{balance:,.0f}" if balance > 0 else "0"
    except Exception as e:
        logger.debug(f"JK balance fetch: {e}")
        return None


async def get_user_lang(telegram_id: int) -> Language:
    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.language if user else Language.RU


@router.message(F.text.in_(["💎 Tonkeeper (TON)"]))
async def ton_connect_handler(message: types.Message, state: FSMContext, db_user: User = None) -> None:
    """Просит отправить адрес TON кошелька."""
    await message.answer(
        "📱 <b>Открой Tonkeeper → скопируй адрес → отправь сюда</b>\n\n"
        "Адрес выглядит так: <code>EQA...или UQA...</code>",
    )
    await state.set_state(TonWalletStates.waiting_address)


@router.message(TonWalletStates.waiting_address, F.text)
async def ton_save_wallet(message: types.Message, state: FSMContext) -> None:
    """Сохраняет адрес и показывает баланс."""
    address = message.text.strip()

    if not validate_ton_address(address):
        await message.answer("❌ Неверный адрес. Отправь EQ... или UQ... (48 символов)")
        return

    # Сохраняем в БД
    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.ton_wallet_address = address
            await session.commit()

    await state.clear()

    # Баланс JK
    jk_balance = await fetch_jk_balance(address)
    balance_text = f"\n💰 <b>JK баланс: {jk_balance} JK</b>" if jk_balance else ""

    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        f"✅ <b>Кошелёк подключён!</b>\n<code>{address[:20]}...{address[-6:]}</code>{balance_text}",
        reply_markup=main_menu_keyboard(lang),
    )
