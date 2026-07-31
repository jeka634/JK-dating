import asyncio, logging, os, random, json, urllib.request
import qrcode
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from pytonconnect import TonConnect
from pytonconnect.storage import IStorage

router = Router(name="ton_wallet")
MANIFEST_URL = "https://raw.githubusercontent.com/NicktoZz/pyton/refs/heads/main/tonconnect-manifest.json"

logger = logging.getLogger(__name__)

JK_TOKEN_CONTRACT = "EQAK3lkmVshzYJeypOCtPBnE_kOJ4Nb9hwyRvQJeRDDW6HPM"


async def fetch_jk_balance(wallet_address: str) -> str | None:
    """Запрашивает баланс JK Coin через TON API."""
    try:
        url = f"https://tonapi.io/v2/accounts/{wallet_address}/jettons/{JK_TOKEN_CONTRACT}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        balance = int(data.get("balance", 0)) / 1e9
        if balance > 0:
            return f"{balance:,.0f}"
        return "0"
    except Exception as e:
        logger.debug(f"JK balance fetch: {e}")
        return None


class TonConnectService:
    """Совместимость со старым кодом. Новый функционал через pytonconnect."""
    async def validate_address(self, address: str) -> bool:
        return bool(address and len(address) >= 48)


class MemoryStorage(IStorage):
    """Хранилище TonConnect в памяти (per-user)."""
    DB = {}

    def __init__(self, user_id: int):
        self.prefix = str(user_id)

    async def set_item(self, key: str, value: str):
        MemoryStorage.DB[self.prefix + key] = value

    async def get_item(self, key: str, default_value: str = None):
        return MemoryStorage.DB.get(self.prefix + key, default_value)

    async def remove_item(self, key: str):
        MemoryStorage.DB.pop(self.prefix + key, None)


async def send_connection_link(message: types.Message, connector: TonConnect) -> types.Message:
    """Генерирует QR-код и кнопку для подключения Tonkeeper."""
    wallets_list = connector.get_wallets()
    # Tonkeeper — обычно первый в списке (индекс 0)
    generated_url = await connector.connect(wallets_list[0])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть Tonkeeper", url=generated_url)]
    ])

    img = qrcode.make(generated_url)
    path = f"/tmp/ton_qr_{random.randint(0, 99999)}.png"
    img.save(path)
    photo = FSInputFile(path)
    msg = await message.answer_photo(photo=photo, caption="Подключи Tonkeeper:", reply_markup=kb)
    os.remove(path)
    return msg


async def get_wallet_address(telegram_id: int) -> str | None:
    """Подключает кошелёк и возвращает адрес или None."""
    connector = TonConnect(manifest_url=MANIFEST_URL, storage=MemoryStorage(telegram_id))
    # Если уже подключён — возвращаем адрес
    if connector.connected and connector.account:
        return connector.account.address
    return None


@router.message(F.text.in_(["💎 Tonkeeper (TON)", "Tonkeeper (TON)", "Tonkeeper"]))
async def connect_wallet_handler(message: types.Message, state: FSMContext):
    """Обработчик кнопки 'Tonkeeper'."""

    connector = TonConnect(manifest_url=MANIFEST_URL, storage=MemoryStorage(message.from_user.id))

    try:
        msg = await send_connection_link(message, connector)
    except Exception as e:
        logger.error(f"TonConnect init error: {e}")
        await message.answer("⚠️ Не удалось создать подключение. Попробуй позже.")
        return

    # Ждём подключения (до 5 минут)
    for _ in range(300):
        await asyncio.sleep(1)
        if connector.connected and connector.account:
            address = connector.account.address
            await msg.delete()

            # Сохраняем в БД
            from app.database.session import get_session
            from app.database.models import User

            async with get_session() as session:
                from sqlalchemy import select, update
                stmt = select(User).where(User.telegram_id == message.from_user.id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    user.ton_wallet_address = address
                    await session.commit()

            await message.answer(f"✅ Кошелёк подключён!\n`{address[:12]}...{address[-6:]}`")

            # Показываем главное меню и баланс JK
            from app.keyboards import main_menu_keyboard
            from app.database.models import Language
            lang = getattr(user, 'language', None) or Language.RU

            # Запрашиваем баланс JK Coin
            jk_balance = await fetch_jk_balance(address)
            if jk_balance:
                await message.answer(
                    f"💰 Баланс JK: {jk_balance} JK\n"
                    f"Адрес: `{address[:15]}...`",
                    reply_markup=main_menu_keyboard(lang),
                )
            else:
                await message.answer(
                    "Проверьте баланс JK в кошельке 👆",
                    reply_markup=main_menu_keyboard(lang),
                )
            return

    await msg.delete()
    await message.answer("⌛ Истекло время подключения. Попробуй ещё раз.")
