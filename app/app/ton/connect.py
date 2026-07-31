"""
Подключение TON кошелька — по аналогии с рабочим ботом.
Использует pytonconnect напрямую: QR-код → ожидание → адрес → баланс JK.
"""
import asyncio, os, random, logging

import qrcode
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from pytonconnect import TonConnect
from pytonconnect.storage import IStorage

from app.database.models import User, Language
from app.database.session import get_session
from app.keyboards import main_menu_keyboard
from sqlalchemy import select

router = Router(name="ton_wallet")
logger = logging.getLogger(__name__)

MANIFEST_URL = "https://raw.githubusercontent.com/NicktoZz/pyton/refs/heads/main/tonconnect-manifest.json"


# ---------- Storage (in-memory) ----------
class MemoryStorage(IStorage):
    DB = {}

    def __init__(self, user_id: int):
        self.prefix = str(user_id)

    async def set_item(self, key: str, value: str):
        MemoryStorage.DB[self.prefix + key] = value

    async def get_item(self, key: str, default_value: str = None):
        return MemoryStorage.DB.get(self.prefix + key, default_value)

    async def remove_item(self, key: str):
        MemoryStorage.DB.pop(self.prefix + key, None)


# ---------- JK баланс ----------
async def fetch_jk_balance(wallet_address: str) -> str | None:
    import json, urllib.request
    JK_TOKEN = "EQAK3lkmVshzYJeypOCtPBnE_kOJ4Nb9hwyRvQJeRDDW6HPM"
    try:
        url = f"https://tonapi.io/v2/accounts/{wallet_address}/jettons/{JK_TOKEN}"
        req = urllib.request.Request(url, headers={"User-Agent": "JK-Dating/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        balance = int(data.get("balance", 0)) / 1e9
        return f"{balance:,.0f}" if balance > 0 else "0"
    except Exception:
        return None


async def save_address(telegram_id: int, address: str) -> Language:
    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.ton_wallet_address = address
            await session.commit()
            return user.language or Language.RU
    return Language.RU


# ---------- QR генерация ----------
async def send_connection_link(message: types.Message, connector: TonConnect):
    wallets_list = connector.get_wallets()
    generated_url = await connector.connect(wallets_list[0])  # Tonkeeper = index 0

    url_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔗 Открыть Tonkeeper", url=generated_url)]]
    )

    img = qrcode.make(generated_url)
    path = f"qr_{random.randint(0, 100000)}.png"
    img.save(path)
    photo = FSInputFile(path)
    msg = await message.answer_photo(photo=photo, caption="📱 Отсканируй QR в Tonkeeper", reply_markup=url_kb)
    os.remove(path)
    return msg


# ---------- Обработчик кнопки ----------
@router.message(F.text.in_(["💎 Tonkeeper (TON)"]))
async def ton_connect_handler(message: types.Message, state: FSMContext) -> None:
    await state.clear()

    connector = TonConnect(
        manifest_url=MANIFEST_URL,
        storage=MemoryStorage(message.from_user.id)
    )

    try:
        msg = await send_connection_link(message, connector)
    except Exception as e:
        logger.error(f"TON Connect init error: {e}")
        await message.answer("⚠️ Ошибка подключения. Попробуй позже.")
        return

    # Ждём подключения (до 5 минут)
    for _ in range(300):
        await asyncio.sleep(1)
        if connector.connected:
            break

    if not connector.account or not connector.account.address:
        await msg.delete()
        await message.answer("⌛ Истекло время. Попробуй ещё раз.")
        return

    address = connector.account.address
    await msg.delete()

    # Сохраняем в БД
    lang = await save_address(message.from_user.id, address)

    # Баланс JK
    jk_balance = await fetch_jk_balance(address)
    balance_line = f"\n💰 <b>JK баланс: {jk_balance} JK</b>" if jk_balance else ""

    await message.answer(
        f"✅ <b>Кошелёк подключён!</b>\n<code>{address[:20]}...{address[-6:]}</code>{balance_line}",
        reply_markup=main_menu_keyboard(lang),
    )
