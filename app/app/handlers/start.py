from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.models import Language, User
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
async def cmd_start(message: Message, db_user: User, state: FSMContext) -> None:
    if db_user.is_blocked:
        await message.answer(get_text("blocked", db_user.language))
        return

    if db_user.is_registered:
        await state.clear()
        await message.answer(
            get_text("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
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
