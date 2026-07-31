from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config.settings import settings
from app.database.models import User
from app.database.repositories.like import LikeRepository
from app.keyboards import main_menu_keyboard, premium_keyboard
from app.payments.stars import StarsPaymentService
from app.services import PremiumService
from app.utils.texts import format_profile, get_text

router = Router(name="premium")

PREMIUM_BUTTON = {"⭐ Premium"}
MY_LIKES_RU = {"💬 Мои лайки"}
MY_LIKES_EN = {"💬 My likes"}


@router.message(F.text.in_(PREMIUM_BUTTON))
async def premium_menu(message: Message, db_user: User) -> None:
    if not db_user.is_registered:
        await message.answer(get_text("not_registered", db_user.language))
        return

    text = get_text(
        "premium_menu",
        db_user.language,
        price=settings.premium_price_stars,
        days=settings.premium_duration_days,
    )
    if db_user.is_premium and db_user.premium_until:
        text += f"\n\n{get_text('premium_active', db_user.language, date=db_user.premium_until.strftime('%d.%m.%Y'))}"

    await message.answer(
        text,
        reply_markup=premium_keyboard(db_user.language, db_user.is_premium),
    )


@router.callback_query(F.data == "premium:buy")
async def premium_buy(callback: CallbackQuery, db_user: User, session: object) -> None:
    stars_service = StarsPaymentService(session)
    payment_id, payload = await stars_service.create_payment(db_user)

    title = "JK Premium" if db_user.language.value == "en" else "JK Premium"
    description = (
        f"Premium subscription for {settings.premium_duration_days} days"
    )

    await callback.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[
            LabeledPrice(
                label="Premium",
                amount=settings.premium_price_stars,
            )
        ],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery) -> None:
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, db_user: User, session: object) -> None:
    payment = message.successful_payment
    stars_service = StarsPaymentService(session)
    user = await stars_service.process_successful_payment(
        payload=payment.invoice_payload,
        telegram_charge_id=payment.telegram_payment_charge_id,
        provider_charge_id=payment.provider_payment_charge_id,
        total_amount=payment.total_amount,
    )
    if user:
        await message.answer(
            get_text("premium_purchased", user.language),
            reply_markup=main_menu_keyboard(user.language),
        )


@router.callback_query(F.data == "premium:boost")
async def premium_boost(
    callback: CallbackQuery, db_user: User, premium_service: PremiumService
) -> None:
    success, reason = await premium_service.boost_profile(db_user)
    if success:
        await callback.answer(
            get_text("profile_boosted", db_user.language), show_alert=True
        )
    elif reason == "cooldown":
        await callback.answer(
            get_text("boost_cooldown", db_user.language), show_alert=True
        )
    else:
        await callback.answer()


@router.callback_query(F.data == "premium:hidden")
async def premium_hidden(
    callback: CallbackQuery, db_user: User, premium_service: PremiumService
) -> None:
    user = await premium_service.toggle_hidden(db_user)
    text = (
        get_text("hidden_mode_on", user.language)
        if user.is_hidden
        else get_text("hidden_mode_off", user.language)
    )
    await callback.answer(text, show_alert=True)


@router.message(F.text.in_(MY_LIKES_RU | MY_LIKES_EN))
async def my_likes(message: Message, db_user: User, session: object) -> None:
    if not db_user.is_registered:
        await message.answer(get_text("not_registered", db_user.language))
        return

    if not db_user.is_premium:
        await message.answer(get_text("premium_only_likes", db_user.language))
        return

    like_repo = LikeRepository(session)
    likes = await like_repo.get_received_likes(db_user.id, limit=10)

    if not likes:
        await message.answer(get_text("no_likes", db_user.language))
        return

    for like in likes:
        if like.from_user:
            text = format_profile(like.from_user, db_user.language)
            photos = sorted(like.from_user.photos, key=lambda p: p.position)
            if photos:
                await message.answer_photo(photos[0].file_id, caption=text)
            else:
                await message.answer(text)
