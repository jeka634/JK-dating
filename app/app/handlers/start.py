from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.models import Gender, Language, User
from app.keyboards import (
    gender_keyboard,
    language_keyboard,
    looking_for_keyboard,
    main_menu_keyboard,
    photos_done_keyboard,
    rules_keyboard,
)
from app.states import RegistrationStates
from app.utils.texts import get_text

router = Router(name="start")


def _resume_registration_state(user: User) -> RegistrationStates:
    if not user.name:
        return RegistrationStates.name
    if not user.age:
        return RegistrationStates.age
    if not user.gender:
        return RegistrationStates.gender
    if not user.looking_for:
        return RegistrationStates.looking_for
    if not user.city:
        return RegistrationStates.city
    if not user.description:
        return RegistrationStates.description
    return RegistrationStates.photos


def _resume_message(user: User, state: RegistrationStates) -> str:
    messages = {
        RegistrationStates.name: "enter_name",
        RegistrationStates.age: "enter_age",
        RegistrationStates.gender: "select_gender",
        RegistrationStates.looking_for: "select_looking_for",
        RegistrationStates.city: "enter_city",
        RegistrationStates.description: "enter_description",
        RegistrationStates.photos: "send_photos",
    }
    return get_text(messages[state], user.language)


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, state: FSMContext, session: object) -> None:
    from datetime import datetime, timezone

    if db_user.is_blocked:
        # Авто-разблокировка после 3 дней
        if db_user.blocked_until and db_user.blocked_until < datetime.now(timezone.utc):
            db_user.is_blocked = False
            db_user.blocked_reason = None
            db_user.blocked_until = None
            db_user.complaints_count = 0
            session.add(db_user)
            await session.commit()
            await state.clear()
            await message.answer(
                get_text("unblocked", db_user.language),
                reply_markup=main_menu_keyboard(db_user.language),
            )
            return

        # Показываем причину блокировки
        from datetime import datetime, timezone
        if db_user.blocked_until:
            unlock_date = db_user.blocked_until.strftime("%d.%m.%Y")
        else:
            unlock_date = "навсегда"
        await message.answer(
            get_text("blocked", db_user.language, reason=db_user.blocked_reason or "жалобы", unlock_date=unlock_date)
        )
        return

    if db_user.is_registered:
        await state.clear()

        # Female users must verify before appearing in search
        if db_user.gender == Gender.FEMALE and not db_user.is_verified:
            await message.answer(
                get_text("female_verify_required", db_user.language),
                reply_markup=main_menu_keyboard(db_user.language),
            )
            return

        await message.answer(
            get_text("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
        return

    # Check username visibility — required for dating
    if not message.from_user.username:
        await message.answer(
            "⚠️ Для знакомств нужен видимый @username.\n\n"
            "Открой Настройки Telegram → Конфиденциальность → Имя пользователя → создай @username.\n\n"
            "Без него тебе не смогут написать при взаимной симпатии. "
            "После создания @username нажми /start снова."
        )
        return

    if db_user.rules_accepted:
        reg_state = _resume_registration_state(db_user)
        text = _resume_message(db_user, reg_state)
        await state.set_state(reg_state)

        if reg_state == RegistrationStates.gender:
            await message.answer(text, reply_markup=gender_keyboard(db_user.language))
        elif reg_state == RegistrationStates.looking_for:
            await message.answer(text, reply_markup=looking_for_keyboard(db_user.language))
        elif reg_state == RegistrationStates.photos:
            await state.update_data(photos=[])
            await message.answer(
                text, reply_markup=photos_done_keyboard(db_user.language)
            )
        else:
            await message.answer(text)
        return

    if db_user.language and db_user.language != Language.RU:
        await message.answer(
            get_text("rules", db_user.language),
            reply_markup=rules_keyboard(db_user.language),
        )
        await state.set_state(RegistrationStates.rules)
        return

    await message.answer(
        get_text("welcome", Language.RU),
        reply_markup=language_keyboard(),
    )
    await state.set_state(RegistrationStates.language)
