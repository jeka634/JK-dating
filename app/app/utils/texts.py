from app.database.models import Gender, Language, LookingFor

TEXTS = {
    Language.RU: {
        "welcome": (
            "🔥 JK Знакомства — эксклюзивный бот знакомств сообщества Jekardos!\n\n"
            "📱 Находи пару, общайся, дружи.\n"
            "⭐ Premium — 199 Stars (безлимитные лайки, кто лайкнул, поднятие анкеты).\n\n"
            "Создай анкету за 2 минуты!\n\n"
            "Выберите язык:"
        ),
        "rules": (
            "📜 Правила использования:\n\n"
            "1. Будьте вежливы и уважайте других пользователей\n"
            "2. Не публикуйте оскорбительный контент\n"
            "3. Используйте только свои фотографии\n"
            "4. Не спамьте и не рекламируйте\n"
            "5. Соблюдайте законы вашей страны\n\n"
            "Нажимая «Принимаю», вы соглашаетесь с правилами."
        ),
        "rules_accepted": "✅ Спасибо! Начнём регистрацию.",
        "enter_name": "📝 Введите ваше имя:",
        "enter_age": "🎂 Введите ваш возраст (от 18 до 99):",
        "invalid_age": "❌ Возраст должен быть от 18 до 99. Попробуйте снова:",
        "select_gender": "👤 Выберите ваш пол:",
        "select_looking_for": "💕 Кого вы ищете?",
        "enter_city": "🏙 Введите ваш город:",
        "enter_description": "📖 Расскажите о себе (до 500 символов):",
        "send_photos": (
            "📸 Отправьте до 5 фотографий.\n"
            "Когда закончите — нажмите «Готово»."
        ),
        "photo_added": "✅ Фото добавлено ({count}/5)",
        "photo_limit": "❌ Максимум 5 фотографий.",
        "registration_complete": "🎉 Регистрация завершена!\n\nДобро пожаловать в JK знакомства!",
        "main_menu": "🏠 Главное меню",
        "browse_no_profiles": "😔 Пока нет подходящих анкет. Попробуйте позже!",
        "like_sent": "❤️ Лайк отправлен!",
        "like_limit": "⏳ Лимит лайков исчерпан ({limit}/день).\nОформите Premium для безлимитных лайков!",
        "mutual_like": "💕 У вас взаимная симпатия с {name}!",
        "mutual_like_notify": "💕 У вас взаимная симпатия ❤️\n\n{name}, {age}, {city}",
        "complaint_sent": "✅ Жалоба отправлена. Мы рассмотрим её в ближайшее время.",
        "enter_complaint_reason": "⛔ Опишите причину жалобы:",
        "my_profile": "👤 Моя анкета",
        "my_likes": "💬 Мои лайки",
        "no_likes": "😔 Пока никто не лайкнул вашу анкету.",
        "premium_only_likes": "⭐ Просмотр лайкнувших доступен только Premium пользователям.",
        "premium_menu": (
            "⭐ Premium подписка\n\n"
            "Преимущества:\n"
            "• Безлимитные лайки\n"
            "• Кто лайкнул\n"
            "• Поднятие анкеты\n"
            "• Приоритет в поиске\n"
            "• Фильтр возраста\n"
            "• Фильтр города\n"
            "• Скрытый режим\n"
            "• Повторный просмотр анкет\n"
            "• История лайков\n\n"
            "Стоимость: {price} ⭐ на {days} дней"
        ),
        "premium_active": "⭐ Premium активен до {date}",
        "premium_purchased": "🎉 Premium успешно активирован!",
        "settings_menu": "⚙️ Настройки",
        "profile_boosted": "🚀 Ваша анкета поднята в поиске!",
        "boost_cooldown": "⏳ Поднятие доступно раз в 24 часа.",
        "hidden_mode_on": "🕶 Скрытый режим включён.",
        "hidden_mode_off": "👁 Скрытый режим выключен.",
        "filter_age_set": "✅ Фильтр возраста: {min}-{max}",
        "filter_city_set": "✅ Фильтр города: {city}",
        "referral_link": (
            "🔗 Ваша реferral ссылка:\n"
            "https://t.me/{bot}?start=ref_{code}\n\n"
            "Приглашено: {count} пользователей"
        ),
        "blocked": "🚫 Ваш аккаунт заблокирован.",
        "not_registered": "❌ Сначала завершите регистрацию.",
        "edit_name": "Введите новое имя:",
        "edit_age": "Введите новый возраст:",
        "edit_city": "Введите новый город:",
        "edit_description": "Введите новое описание:",
        "profile_updated": "✅ Анкета обновлена!",
        "gender_male": "Мужской",
        "gender_female": "Женский",
        "gender_other": "Другой",
        "looking_male": "Мужчин",
        "looking_female": "Женщин",
        "looking_all": "Всех",
        "ton_wallet_connected": "✅ TON кошелёк подключён: {address}",
        "ton_balance": "💎 Баланс $JK: {balance}",
        "ton_not_connected": "❌ TON кошелёк не подключён.",
    },
    Language.EN: {
        "welcome": "👋 Welcome to JK Dating!\n\nChoose your language:",
        "rules": (
            "📜 Terms of Use:\n\n"
            "1. Be polite and respect other users\n"
            "2. Do not publish offensive content\n"
            "3. Use only your own photos\n"
            "4. Do not spam or advertise\n"
            "5. Follow the laws of your country\n\n"
            "By clicking «Accept», you agree to the rules."
        ),
        "rules_accepted": "✅ Thank you! Let's start registration.",
        "enter_name": "📝 Enter your name:",
        "enter_age": "🎂 Enter your age (18 to 99):",
        "invalid_age": "❌ Age must be between 18 and 99. Try again:",
        "select_gender": "👤 Select your gender:",
        "select_looking_for": "💕 Who are you looking for?",
        "enter_city": "🏙 Enter your city:",
        "enter_description": "📖 Tell us about yourself (up to 500 chars):",
        "send_photos": (
            "📸 Send up to 5 photos.\n"
            "When done — press «Done»."
        ),
        "photo_added": "✅ Photo added ({count}/5)",
        "photo_limit": "❌ Maximum 5 photos.",
        "registration_complete": "🎉 Registration complete!\n\nWelcome to JK Dating!",
        "main_menu": "🏠 Main menu",
        "browse_no_profiles": "😔 No matching profiles yet. Try again later!",
        "like_sent": "❤️ Like sent!",
        "like_limit": "⏳ Daily like limit reached ({limit}/day).\nGet Premium for unlimited likes!",
        "mutual_like": "💕 You have a mutual match with {name}!",
        "mutual_like_notify": "💕 You have a mutual match ❤️\n\n{name}, {age}, {city}",
        "complaint_sent": "✅ Complaint submitted. We will review it shortly.",
        "enter_complaint_reason": "⛔ Describe the reason for your complaint:",
        "my_profile": "👤 My profile",
        "my_likes": "💬 My likes",
        "no_likes": "😔 No one has liked your profile yet.",
        "premium_only_likes": "⭐ Viewing likes is available for Premium users only.",
        "premium_menu": (
            "⭐ Premium subscription\n\n"
            "Benefits:\n"
            "• Unlimited likes\n"
            "• See who liked you\n"
            "• Profile boost\n"
            "• Search priority\n"
            "• Age filter\n"
            "• City filter\n"
            "• Hidden mode\n"
            "• Re-browse profiles\n"
            "• Like history\n\n"
            "Price: {price} ⭐ for {days} days"
        ),
        "premium_active": "⭐ Premium active until {date}",
        "premium_purchased": "🎉 Premium successfully activated!",
        "settings_menu": "⚙️ Settings",
        "profile_boosted": "🚀 Your profile has been boosted!",
        "boost_cooldown": "⏳ Boost available once every 24 hours.",
        "hidden_mode_on": "🕶 Hidden mode enabled.",
        "hidden_mode_off": "👁 Hidden mode disabled.",
        "filter_age_set": "✅ Age filter: {min}-{max}",
        "filter_city_set": "✅ City filter: {city}",
        "referral_link": (
            "🔗 Your referral link:\n"
            "https://t.me/{bot}?start=ref_{code}\n\n"
            "Invited: {count} users"
        ),
        "blocked": "🚫 Your account has been blocked.",
        "not_registered": "❌ Please complete registration first.",
        "edit_name": "Enter new name:",
        "edit_age": "Enter new age:",
        "edit_city": "Enter new city:",
        "edit_description": "Enter new description:",
        "profile_updated": "✅ Profile updated!",
        "gender_male": "Male",
        "gender_female": "Female",
        "gender_other": "Other",
        "looking_male": "Men",
        "looking_female": "Women",
        "looking_all": "Everyone",
        "ton_wallet_connected": "✅ TON wallet connected: {address}",
        "ton_balance": "💎 $JK Balance: {balance}",
        "ton_not_connected": "❌ TON wallet not connected.",
    },
}


def get_text(key: str, language: Language, **kwargs: object) -> str:
    lang_texts = TEXTS.get(language, TEXTS[Language.RU])
    text = lang_texts.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def format_profile(user: object, language: Language) -> str:
    from app.database.models import User

    if not isinstance(user, User):
        return ""

    gender_map = {
        Gender.MALE: get_text("gender_male", language),
        Gender.FEMALE: get_text("gender_female", language),
        Gender.OTHER: get_text("gender_other", language),
    }
    gender_text = gender_map.get(user.gender, "") if user.gender else ""

    lines = [
        f"👤 {user.name}, {user.age}",
        f"🏙 {user.city}",
    ]
    if gender_text:
        lines.append(f"⚧ {gender_text}")
    if user.description:
        lines.append(f"\n{user.description}")
    if user.is_premium:
        lines.append("\n⭐ Premium")
    return "\n".join(lines)
