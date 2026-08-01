from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.models import Language, User
from app.database.repositories.user import UserRepository
from app.keyboards import (
    cancel_keyboard,
    main_menu_keyboard,
    photos_done_keyboard,
    profile_actions_keyboard,
    settings_keyboard,
)
from app.services import UserService
from app.states import EditProfileStates, FilterStates, RegistrationStates
from app.utils.redis_cache import redis_cache
from app.utils.texts import format_profile, get_text

router = Router(name="settings")

PROFILE_BUTTONS_RU = {"👤 Моя анкета"}
PROFILE_BUTTONS_EN = {"👤 My profile"}
SETTINGS_BUTTONS_RU = {"⚙️ Настройки"}
SETTINGS_BUTTONS_EN = {"⚙️ Settings"}
CANCEL_BUTTONS = {"❌ Отмена", "❌ Cancel"}


@router.message(F.text.in_(PROFILE_BUTTONS_RU | PROFILE_BUTTONS_EN))
async def my_profile(message: Message, db_user: User) -> None:
    if not db_user.is_registered:
        await message.answer(get_text("not_registered", db_user.language))
        return

    text = format_profile(db_user, db_user.language)
    photos = sorted(db_user.photos, key=lambda p: p.position)
    if photos:
        await message.answer_photo(
            photos[0].file_id,
            caption=text,
            reply_markup=profile_actions_keyboard(db_user.language),
        )
    else:
        await message.answer(
            text,
            reply_markup=profile_actions_keyboard(db_user.language),
        )


@router.message(F.text.in_(SETTINGS_BUTTONS_RU | SETTINGS_BUTTONS_EN))
async def settings_menu(message: Message, db_user: User) -> None:
    if not db_user.is_registered:
        await message.answer(get_text("not_registered", db_user.language))
        return

    await message.answer(
        get_text("settings_menu", db_user.language),
        reply_markup=settings_keyboard(db_user.language, db_user.is_premium),
    )


@router.callback_query(F.data == "profile:edit")
async def profile_edit(callback: CallbackQuery, db_user: User) -> None:
    await callback.message.edit_reply_markup(
        reply_markup=settings_keyboard(db_user.language, db_user.is_premium)
    )
    await callback.answer()


@router.callback_query(F.data == "profile:reset")
async def profile_reset(
    callback: CallbackQuery, db_user: User, state: FSMContext, session: object
) -> None:
    """Полный сброс анкеты: очищает все поля и запускает регистрацию заново."""
    from app.database.repositories.user import UserRepository

    repo = UserRepository(session)
    await repo.reset_profile(db_user.id)

    # Очищаем FSM и начинаем регистрацию с языка
    await state.clear()
    db_user.is_registered = False
    db_user.name = None
    db_user.age = None
    db_user.gender = None
    db_user.looking_for = None
    db_user.city = None
    db_user.description = None

    confirm_text = (
        "🔄 Анкета сброшена. Давай заполним её заново!\n\n📝 Введите ваше имя:"
        if db_user.language == Language.RU
        else "🔄 Profile reset. Let's fill it again!\n\n📝 Enter your name:"
    )
    # Профиль отображается как фото с caption — используем edit_caption
    try:
        await callback.message.edit_caption(caption=confirm_text)
    except Exception:
        await callback.message.edit_text(confirm_text)
    await state.set_state(RegistrationStates.name)
    await callback.answer("🔄 Анкета сброшена!", show_alert=True)


@router.callback_query(F.data == "menu:back")
async def menu_back(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        get_text("main_menu", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:name")
async def edit_name(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await callback.message.answer(
        get_text("edit_name", db_user.language),
        reply_markup=cancel_keyboard(db_user.language),
    )
    await state.set_state(EditProfileStates.name)
    await callback.answer()


@router.message(EditProfileStates.name, F.text)
async def save_name(message: Message, db_user: User, state: FSMContext) -> None:
    if message.text in CANCEL_BUTTONS:
        await state.clear()
        await message.answer(
            get_text("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
        return
    db_user.name = message.text.strip()[:50]
    await state.clear()
    await message.answer(
        get_text("profile_updated", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )


@router.callback_query(F.data == "edit:age")
async def edit_age(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await callback.message.answer(
        get_text("edit_age", db_user.language),
        reply_markup=cancel_keyboard(db_user.language),
    )
    await state.set_state(EditProfileStates.age)
    await callback.answer()


@router.message(EditProfileStates.age, F.text)
async def save_age(message: Message, db_user: User, state: FSMContext) -> None:
    if message.text in CANCEL_BUTTONS:
        await state.clear()
        await message.answer(
            get_text("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
        return
    try:
        age = int(message.text.strip())
        if 18 <= age <= 99:
            db_user.age = age
    except ValueError:
        pass
    await state.clear()
    await message.answer(
        get_text("profile_updated", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )


@router.callback_query(F.data == "edit:city")
async def edit_city(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await callback.message.answer(
        get_text("edit_city", db_user.language),
        reply_markup=cancel_keyboard(db_user.language),
    )
    await state.set_state(EditProfileStates.city)
    await callback.answer()


@router.message(EditProfileStates.city, F.text)
async def save_city(message: Message, db_user: User, state: FSMContext) -> None:
    if message.text in CANCEL_BUTTONS:
        await state.clear()
        await message.answer(
            get_text("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
        return
    db_user.city = message.text.strip()[:100]
    await state.clear()
    await message.answer(
        get_text("profile_updated", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )


@router.callback_query(F.data == "edit:description")
async def edit_description(
    callback: CallbackQuery, db_user: User, state: FSMContext
) -> None:
    await callback.message.answer(
        get_text("edit_description", db_user.language),
        reply_markup=cancel_keyboard(db_user.language),
    )
    await state.set_state(EditProfileStates.description)
    await callback.answer()


@router.message(EditProfileStates.description, F.text)
async def save_description(
    message: Message, db_user: User, state: FSMContext
) -> None:
    if message.text in CANCEL_BUTTONS:
        await state.clear()
        await message.answer(
            get_text("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )
        return
    db_user.description = message.text.strip()[:500]
    await state.clear()
    await message.answer(
        get_text("profile_updated", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )


@router.callback_query(F.data == "edit:photos")
async def edit_photos(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    await state.update_data(photos=[])
    await callback.message.answer(
        get_text("send_photos", db_user.language),
        reply_markup=photos_done_keyboard(db_user.language),
    )
    await state.set_state(EditProfileStates.photos)
    await callback.answer()


@router.message(EditProfileStates.photos, F.photo)
async def edit_photo_add(message: Message, db_user: User, state: FSMContext) -> None:
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


@router.callback_query(EditProfileStates.photos, F.data == "photos:done")
async def edit_photos_done(
    callback: CallbackQuery, db_user: User, state: FSMContext, session: object
) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    if photos:
        user_repo = UserRepository(session)
        await user_repo.delete_photos(db_user.id)
        for idx, photo_data in enumerate(photos):
            await user_repo.add_photo(
                db_user.id,
                photo_data["file_id"],
                photo_data["file_unique_id"],
                idx,
            )
    await state.clear()
    await callback.message.edit_text(get_text("profile_updated", db_user.language))
    await callback.message.answer(
        get_text("main_menu", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )
    await callback.answer()


@router.callback_query(F.data == "filter:age")
async def filter_age(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    if not db_user.is_premium:
        await callback.answer()
        return
    await callback.message.answer("Min age (18-99):")
    await state.set_state(FilterStates.age_min)
    await callback.answer()


@router.message(FilterStates.age_min, F.text)
async def filter_age_min(message: Message, db_user: User, state: FSMContext) -> None:
    try:
        age_min = int(message.text.strip())
        if 18 <= age_min <= 99:
            await state.update_data(age_min=age_min)
            await message.answer("Max age (18-99):")
            await state.set_state(FilterStates.age_max)
            return
    except ValueError:
        pass
    await message.answer("Min age (18-99):")


@router.message(FilterStates.age_max, F.text)
async def filter_age_max(message: Message, db_user: User, state: FSMContext) -> None:
    data = await state.get_data()
    age_min = data.get("age_min", 18)
    try:
        age_max = int(message.text.strip())
        if age_min <= age_max <= 99:
            db_user.filter_age_min = age_min
            db_user.filter_age_max = age_max
            await state.clear()
            await message.answer(
                get_text(
                    "filter_age_set",
                    db_user.language,
                    min=age_min,
                    max=age_max,
                ),
                reply_markup=main_menu_keyboard(db_user.language),
            )
            return
    except ValueError:
        pass
    await message.answer("Max age (18-99):")


@router.callback_query(F.data == "filter:city")
async def filter_city(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    if not db_user.is_premium:
        await callback.answer()
        return
    await callback.message.answer("Enter city filter:")
    await state.set_state(FilterStates.city)
    await callback.answer()


@router.message(FilterStates.city, F.text)
async def filter_city_save(message: Message, db_user: User, state: FSMContext) -> None:
    db_user.filter_city = message.text.strip()[:100]
    await state.clear()
    await message.answer(
        get_text("filter_city_set", db_user.language, city=db_user.filter_city),
        reply_markup=main_menu_keyboard(db_user.language),
    )


@router.callback_query(F.data == "settings:referral")
async def settings_referral(
    callback: CallbackQuery, db_user: User, user_service: UserService
) -> None:
    from app.config.settings import settings

    code, count = await user_service.get_referral_stats(db_user)
    bot_username = settings.bot_username or "jk_dating_bot"
    text = get_text(
        "referral_link",
        db_user.language,
        bot=bot_username,
        code=code,
        count=count,
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "settings:rebrowse")
async def settings_rebrowse(callback: CallbackQuery, db_user: User) -> None:
    if not db_user.is_premium:
        await callback.answer()
        return
    await redis_cache.clear_browse_exclude(db_user.id)
    await callback.answer("✅", show_alert=True)
