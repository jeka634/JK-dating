from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.models import Gender, Language, LookingFor, User
from app.keyboards import (
    gender_keyboard,
    looking_for_keyboard,
    main_menu_keyboard,
    photos_done_keyboard,
    rules_keyboard,
)
from app.states import RegistrationStates
from app.utils.texts import get_text
from app.utils.moderation import contains_bad_words

router = Router(name="registration")


@router.callback_query(RegistrationStates.language, F.data.startswith("lang:"))
async def process_language(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    lang_code = callback.data.split(":")[1]
    language = Language.RU if lang_code == "ru" else Language.EN
    db_user.language = language
    await callback.message.edit_text(
        get_text("rules", language),
        reply_markup=rules_keyboard(language),
    )
    await state.set_state(RegistrationStates.rules)
    await callback.answer()


@router.callback_query(RegistrationStates.rules, F.data == "rules:accept")
async def process_rules(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    db_user.rules_accepted = True
    await callback.message.edit_text(get_text("rules_accepted", db_user.language))
    await callback.message.answer(get_text("enter_name", db_user.language))
    await state.set_state(RegistrationStates.name)
    await callback.answer()


@router.message(RegistrationStates.name, F.text)
async def process_name(message: Message, db_user: User, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer(get_text("enter_name", db_user.language))
        return
    if contains_bad_words(name):
        await message.answer("❌ Имя содержит недопустимые слова. Введи другое.")
        return
    db_user.name = name
    await message.answer(get_text("enter_age", db_user.language))
    await state.set_state(RegistrationStates.age)


@router.message(RegistrationStates.age, F.text)
async def process_age(message: Message, db_user: User, state: FSMContext) -> None:
    try:
        age = int(message.text.strip())
    except ValueError:
        await message.answer(get_text("invalid_age", db_user.language))
        return
    if age < 18 or age > 99:
        await message.answer(get_text("invalid_age", db_user.language))
        return
    db_user.age = age
    await message.answer(
        get_text("select_gender", db_user.language),
        reply_markup=gender_keyboard(db_user.language),
    )
    await state.set_state(RegistrationStates.gender)


@router.callback_query(RegistrationStates.gender, F.data.startswith("gender:"))
async def process_gender(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    gender_map = {
        "male": Gender.MALE,
        "female": Gender.FEMALE,
        "other": Gender.OTHER,
    }
    db_user.gender = gender_map[callback.data.split(":")[1]]
    await callback.message.edit_text(get_text("select_looking_for", db_user.language))
    await callback.message.edit_reply_markup(
        reply_markup=looking_for_keyboard(db_user.language)
    )
    await state.set_state(RegistrationStates.looking_for)
    await callback.answer()


@router.callback_query(RegistrationStates.looking_for, F.data.startswith("looking:"))
async def process_looking_for(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    looking_map = {
        "male": LookingFor.MALE,
        "female": LookingFor.FEMALE,
        "all": LookingFor.ALL,
    }
    db_user.looking_for = looking_map[callback.data.split(":")[1]]
    await callback.message.edit_text(get_text("enter_city", db_user.language))
    await state.set_state(RegistrationStates.city)
    await callback.answer()


@router.message(RegistrationStates.city, F.text)
async def process_city(message: Message, db_user: User, state: FSMContext) -> None:
    city = message.text.strip()
    if len(city) < 2 or len(city) > 100:
        await message.answer(get_text("enter_city", db_user.language))
        return
    db_user.city = city
    await message.answer(get_text("enter_description", db_user.language))
    await state.set_state(RegistrationStates.description)


@router.message(RegistrationStates.description, F.text)
async def process_description(
    message: Message, db_user: User, state: FSMContext
) -> None:
    description = message.text.strip()
    if contains_bad_words(description):
        await message.answer("❌ Описание содержит недопустимые слова. Напиши другое.")
        return
    if len(description) > 500:
        description = description[:500]
    db_user.description = description
    await state.update_data(photos=[])
    await message.answer(
        get_text("send_photos", db_user.language),
        reply_markup=photos_done_keyboard(db_user.language),
    )
    await state.set_state(RegistrationStates.photos)


@router.message(RegistrationStates.photos, F.photo)
async def process_photo(message: Message, db_user: User, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 5:
        await message.answer(get_text("photo_limit", db_user.language))
        return
    photo = message.photo[-1]
    photos.append({"file_id": photo.file_id, "file_unique_id": photo.file_unique_id})
    await state.update_data(photos=photos)
    await message.answer(
        get_text("photo_added", db_user.language, count=len(photos)),
        reply_markup=photos_done_keyboard(db_user.language),
    )


@router.callback_query(RegistrationStates.photos, F.data == "photos:done")
async def process_photos_done(
    callback: CallbackQuery,
    db_user: User,
    state: FSMContext,
    user_service: object,
) -> None:
    from app.services import UserService

    data = await state.get_data()
    photos = data.get("photos", [])
    if not photos:
        await callback.answer(get_text("send_photos", db_user.language))
        return

    service: UserService = user_service
    for idx, photo_data in enumerate(photos):
        await service.user_repo.add_photo(
            db_user.id,
            photo_data["file_id"],
            photo_data["file_unique_id"],
            idx,
        )

    await service.complete_registration(db_user)
    await state.clear()
    await callback.message.edit_text(
        get_text("registration_complete", db_user.language)
    )
    await callback.message.answer(
        get_text("main_menu", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )
    await callback.answer()
