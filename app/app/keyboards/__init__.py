from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.database.models import Gender, Language, LookingFor
from app.utils.texts import get_text


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    return builder.as_markup()


def rules_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    accept_text = "✅ Принимаю" if language == Language.RU else "✅ Accept"
    builder.row(
        InlineKeyboardButton(text=accept_text, callback_data="rules:accept")
    )
    return builder.as_markup()


def gender_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("gender_male", language),
            callback_data="gender:male",
        ),
        InlineKeyboardButton(
            text=get_text("gender_female", language),
            callback_data="gender:female",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("gender_other", language),
            callback_data="gender:other",
        )
    )
    return builder.as_markup()


def looking_for_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("looking_male", language),
            callback_data="looking:male",
        ),
        InlineKeyboardButton(
            text=get_text("looking_female", language),
            callback_data="looking:female",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("looking_all", language),
            callback_data="looking:all",
        )
    )
    return builder.as_markup()


def photos_done_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text = "✅ Готово" if language == Language.RU else "✅ Done"
    builder.row(InlineKeyboardButton(text=text, callback_data="photos:done"))
    return builder.as_markup()


def main_menu_keyboard(language: Language) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if language == Language.RU:
        builder.row(
            KeyboardButton(text="❤️ Смотреть анкеты"),
            KeyboardButton(text="💬 Мои лайки"),
        )
        builder.row(
            KeyboardButton(text="⭐ Premium"),
            KeyboardButton(text="👤 Моя анкета"),
        )
        builder.row(
            KeyboardButton(text="⚙️ Настройки"),
        )
        builder.row(KeyboardButton(text="💎 Tonkeeper (TON)"))
    else:
        builder.row(
            KeyboardButton(text="❤️ Browse profiles"),
            KeyboardButton(text="💬 My likes"),
        )
        builder.row(
            KeyboardButton(text="⭐ Premium"),
            KeyboardButton(text="👤 My profile"),
        )
        builder.row(
            KeyboardButton(text="⚙️ Settings"),
        )
        builder.row(KeyboardButton(text="💎 Tonkeeper (TON)"))
    return builder.as_markup(resize_keyboard=True)


def browse_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    like_text = "❤️ Лайк" if language == Language.RU else "❤️ Like"
    skip_text = "👎 Далее" if language == Language.RU else "👎 Next"
    report_text = "⛔ Жалоба" if language == Language.RU else "⛔ Report"
    builder.row(
        InlineKeyboardButton(text=like_text, callback_data="browse:like"),
        InlineKeyboardButton(text=skip_text, callback_data="browse:skip"),
    )
    builder.row(
        InlineKeyboardButton(text=report_text, callback_data="browse:report")
    )
    return builder.as_markup()


def premium_keyboard(language: Language, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_premium:
        buy_text = "⭐ Купить Premium" if language == Language.RU else "⭐ Buy Premium"
        builder.row(
            InlineKeyboardButton(text=buy_text, callback_data="premium:buy")
        )
    else:
        boost_text = "🚀 Поднять анкету" if language == Language.RU else "🚀 Boost profile"
        hidden_text = (
            "🕶 Скрытый режим" if language == Language.RU else "🕶 Hidden mode"
        )
        builder.row(
            InlineKeyboardButton(text=boost_text, callback_data="premium:boost")
        )
        builder.row(
            InlineKeyboardButton(text=hidden_text, callback_data="premium:hidden")
        )
    back_text = "◀️ Назад" if language == Language.RU else "◀️ Back"
    builder.row(InlineKeyboardButton(text=back_text, callback_data="menu:back"))
    return builder.as_markup()


def settings_keyboard(language: Language, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if language == Language.RU:
        builder.row(
            InlineKeyboardButton(text="✏️ Имя", callback_data="edit:name"),
            InlineKeyboardButton(text="🎂 Возраст", callback_data="edit:age"),
        )
        builder.row(
            InlineKeyboardButton(text="🏙 Город", callback_data="edit:city"),
            InlineKeyboardButton(text="📖 Описание", callback_data="edit:description"),
        )
        builder.row(
            InlineKeyboardButton(text="📸 Фото", callback_data="edit:photos"),
        )
        if is_premium:
            builder.row(
                InlineKeyboardButton(
                    text="🔍 Фильтр возраста", callback_data="filter:age"
                ),
                InlineKeyboardButton(
                    text="🏙 Фильтр города", callback_data="filter:city"
                ),
            )
        builder.row(
            InlineKeyboardButton(text="🔗 Реферальная ссылка", callback_data="settings:referral")
        )
        builder.row(
            InlineKeyboardButton(text="💎 TON кошелёк", callback_data="settings:ton")
        )
        builder.row(
            InlineKeyboardButton(text="🔄 Повторный просмотр", callback_data="settings:rebrowse")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✏️ Name", callback_data="edit:name"),
            InlineKeyboardButton(text="🎂 Age", callback_data="edit:age"),
        )
        builder.row(
            InlineKeyboardButton(text="🏙 City", callback_data="edit:city"),
            InlineKeyboardButton(text="📖 Description", callback_data="edit:description"),
        )
        builder.row(
            InlineKeyboardButton(text="📸 Photos", callback_data="edit:photos"),
        )
        if is_premium:
            builder.row(
                InlineKeyboardButton(
                    text="🔍 Age filter", callback_data="filter:age"
                ),
                InlineKeyboardButton(
                    text="🏙 City filter", callback_data="filter:city"
                ),
            )
        builder.row(
            InlineKeyboardButton(text="🔗 Referral link", callback_data="settings:referral")
        )
        builder.row(
            InlineKeyboardButton(text="💎 TON wallet", callback_data="settings:ton")
        )
        builder.row(
            InlineKeyboardButton(text="🔄 Re-browse", callback_data="settings:rebrowse")
        )
    back_text = "◀️ Назад" if language == Language.RU else "◀️ Back"
    builder.row(InlineKeyboardButton(text=back_text, callback_data="menu:back"))
    return builder.as_markup()


def profile_actions_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    edit_text = "✏️ Редактировать" if language == Language.RU else "✏️ Edit"
    builder.row(
        InlineKeyboardButton(text=edit_text, callback_data="profile:edit")
    )
    back_text = "◀️ Назад" if language == Language.RU else "◀️ Back"
    builder.row(InlineKeyboardButton(text=back_text, callback_data="menu:back"))
    return builder.as_markup()


def cancel_keyboard(language: Language) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    text = "❌ Отмена" if language == Language.RU else "❌ Cancel"
    builder.row(KeyboardButton(text=text))
    return builder.as_markup(resize_keyboard=True)


def ton_wallet_keyboard(language: Language) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    connect_text = (
        "🔗 Подключить кошелёк" if language == Language.RU else "🔗 Connect wallet"
    )
    balance_text = (
        "💎 Проверить баланс $JK" if language == Language.RU else "💎 Check $JK balance"
    )
    builder.row(
        InlineKeyboardButton(text=connect_text, callback_data="ton:connect")
    )
    builder.row(
        InlineKeyboardButton(text=balance_text, callback_data="ton:balance")
    )
    back_text = "◀️ Назад" if language == Language.RU else "◀️ Back"
    builder.row(InlineKeyboardButton(text=back_text, callback_data="menu:back"))
    return builder.as_markup()
