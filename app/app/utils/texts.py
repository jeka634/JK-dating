"""JK Dating — локализованные тексты."""

from app.database.models import Language

TEXTS_RU = {
    "welcome": "👋 Добро пожаловать в JK Dating!\n\nВыберите язык:",
    "rules": (
        "📜 Правила использования:\n\n"
        "1. Будьте вежливы и уважайте друг друга\n"
        "2. Не публикуйте оскорбительный контент\n"
        "3. Используйте только свои фото\n"
        "4. Не спамьте и не рекламируйте\n"
        "5. Соблюдайте законы вашей страны\n\n"
        "Нажимая «Принять», вы соглашаетесь с правилами."
    ),
    "rules_accepted": "✅ Спасибо! Давайте начнём регистрацию.",
    "enter_name": "📝 Введите ваше имя:",
    "enter_age": "🎂 Введите ваш возраст (от 18 до 99):",
    "select_gender": "⚤ Выберите пол:",
    "select_looking_for": "🔍 Кого вы ищете?",
    "enter_city": "🏙 Введите город:",
    "enter_description": "📖 Расскажите о себе (до 500 символов):",
    "send_photos": "📸 Отправьте ВАШИ РЕАЛЬНЫЕ фото (до 5 штук):\n\n⚠️ Запрещено:\n• Фото природы, животных, мемов\n• Чужие фото из интернета\n• Скриншоты и коллажи\n• Размытые/обрезанные снимки\n\nНарушители блокируются по жалобам.",
    "photo_added": "✅ Фото {count}/5 добавлено. Ещё? (нажмите «Готово» когда закончите)",
    "photo_limit": "❌ Максимум 5 фото.",
    "main_menu": "📋 Главное меню:",
    "settings_menu": "⚙️ Настройки профиля:",
    "not_registered": "❌ Сначала завершите регистрацию.",
    "female_verify_required": "⚠️ Твой профиль скрыт из поиска, пока не пройдена верификация.\n\nОтправь селфи с жестом ✌️ (палец к носу) — одно фото, где видно лицо и жест.\n\nЭто защита от фейков. После проверки твоя анкета станет видна.",
    "profile_updated": "✅ Профиль обновлён!",
    "no_profiles": "😔 Анкет больше нет. Попробуйте позже.",
    "browse_no_profiles": "🔍 Анкет не найдено!\n\nПопробуйте позже или измените критерии поиска в настройках.",
    "browse_start": "🔍 Ищем анкеты...\n❤️ — лайк\n👎 — пропустить\n📝 — жалоба",
    "boost_cooldown": "⏳ Поднятие анкеты доступно раз в 24 часа. Доступно через {hours} ч.",
    "invalid_age": "❌ Некорректный возраст. Введите число от 18 до 99.",
    "premium_purchased": "✅ Премиум куплен!",
    "premium_only_likes": "⭐ Только премиум-пользователи могут ставить лайки.",
    "registration_complete": "✅ Регистрация завершена! Добро пожаловать в JK Dating!",
    "mutual_like": "🎉 Взаимный лайк с {name}, {age} лет, {city}!\n\nНапишите @{username} чтобы начать общение.",
    "no_likes": "❤️ У вас пока нет лайков. Ищите анкеты и ставьте лайки!",
    "complaint_sent": "✅ Жалоба отправлена. Спасибо за бдительность!",
    "enter_complaint_reason": "📝 Опишите причину жалобы:",
    "mutual_like_notify": "🎉 Взаимный лайк с {name}, {age} лет, {city}!\n\nНапишите: {username_link}",
    "like_sent": "❤️ Лайк отправлен!",
    "like_limit": "❌ Лимит лайков на сегодня исчерпан ({limit}). Premium снимает ограничения.",
    "new_user_like_limit": "⚠️ Новые пользователи: лимит {limit} лайков в первые {hours}ч. Premium снимает ограничения.",
    "skip_profile": "👎 Пропущено.",
    "premium_menu": "⭐ Premium\n\nПремиум даёт:\n• Неограниченные лайки\n• Фильтры по возрасту и городу\n• Поднятие анкеты\n• Скрытый режим\n• Защита от автоблокировки (3 жалобы = блок на 3 дня, без премиума — навсегда)\n\n⚠️ Политика: 3 жалобы = авто-блок. Без премиума — навсегда. С премиумом — 3 дня.",
    "premium_buy": "⭐ Купить Premium за {price} ⭐",
    "premium_success": "✅ Premium активирован! Действует {days} дн.",
    "already_premium": "⭐ У вас уже есть Premium до {date}.",
    "profile_boosted": "🚀 Анкета поднята! Теперь вы в топе.",
    "hidden_mode_on": "🕶 Скрытый режим включён. Вашу анкету видят только те, кому вы поставили лайк.",
    "hidden_mode_off": "👁 Скрытый режим выключен.",
    "filter_age_set": "✅ Фильтр возраста: {min}-{max}",
    "filter_city_set": "✅ Фильтр города: {city}",
    "referral_link": (
        "🔗 Ваша реферальная ссылка:\n"
        "https://t.me/{bot}?start=ref_{code}\n\n"
        "Приглашено: {count} пользователей"
    ),
    "blocked": "🚫 Ваша анкета заблокирована.\n\nПричина: {reason}\nРазблокировка: {unlock_date}\n\n⭐ Разблокировка возможна только при наличии премиум-подписки.",
    "unblocked": "✅ Ваша анкета разблокирована! Добро пожаловать обратно.",
    "of": "из",
    "edit_name": "Введите новое имя:",
    "edit_age": "Введите новый возраст:",
    "edit_city": "Введите новый город:",
    "edit_description": "Введите новое описание:",
    "gender_male": "Мужской",
    "gender_female": "Женский",
    "gender_other": "Другой",
    "looking_male": "Мужчин",
    "looking_female": "Женщин",
    "looking_all": "Всех",
}

TEXTS_EN = {
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
    "select_gender": "⚤ Select gender:",
    "select_looking_for": "🔍 Who are you looking for?",
    "enter_city": "🏙 Enter your city:",
    "enter_description": "📖 Tell us about yourself (up to 500 chars):",
    "send_photos": "📸 Send YOUR REAL photos (up to 5):\n\n⚠️ Not allowed:\n• Nature, animals, memes\n• Other people's photos from internet\n• Screenshots and collages\n• Blurry/cropped images\n\nViolators are blocked by complaints.",
    "photo_added": "✅ Photo {count}/5 added. Send more? (press «Done» when finished)",
    "photo_limit": "❌ Maximum 5 photos.",
    "main_menu": "📋 Main menu:",
    "settings_menu": "⚙️ Profile settings:",
    "not_registered": "❌ Please complete registration first.",
    "female_verify_required": "⚠️ Your profile is hidden until verified.\n\nSend a selfie with ✌️ gesture (finger to nose) — one photo showing your face and the gesture.\n\nThis protects against fakes. Your profile will become visible after verification.",
    "profile_updated": "✅ Profile updated!",
    "no_profiles": "😔 No more profiles. Try later.",
    "complaint_sent": "✅ Complaint submitted. Thank you!",
    "enter_complaint_reason": "📝 Describe the reason for your complaint:",
    "mutual_like": "🎉 Mutual like with {name}, {age}, {city}!\n\nWrite @{username} to start chatting.",
    "mutual_like_notify": "🎉 Mutual like with {name}, {age}, {city}!\n\nWrite to: {username_link}",
    "like_sent": "❤️ Like sent!",
    "like_limit": "❌ Daily like limit reached ({limit}). Premium removes limits.",
    "new_user_like_limit": "⚠️ New users: {limit} likes limit for first {hours}h. Premium removes limits.",
    "skip_profile": "👎 Skipped.",
    "premium_menu": "⭐ Premium\n\nPremium gives you:\n• Unlimited likes\n• Age and city filters\n• Profile boost\n• Hidden mode\n• Anti-block protection (3 complaints = 3-day block, without premium — forever)\n\n⚠️ Policy: 3 complaints = auto-block. No premium → forever. With premium → 3 days.",
    "premium_buy": "⭐ Buy Premium for {price} ⭐",
    "premium_success": "✅ Premium activated! Valid for {days} days.",
    "already_premium": "⭐ You already have Premium until {date}.",
    "profile_boosted": "🚀 Profile boosted! You're now on top.",
    "hidden_mode_on": "🕶 Hidden mode on. Only people you liked can see your profile.",
    "hidden_mode_off": "👁 Hidden mode off.",
    "filter_age_set": "✅ Age filter: {min}-{max}",
    "filter_city_set": "✅ City filter: {city}",
    "referral_link": (
        "🔗 Your referral link:\n"
        "https://t.me/{bot}?start=ref_{code}\n\n"
        "Invited: {count} users"
    ),
    "blocked": "🚫 Your profile has been blocked.\n\nReason: {reason}\nUnlock: {unlock_date}\n\n⭐ Unlock is only available with Premium subscription.",
    "unblocked": "✅ Your profile has been unlocked! Welcome back.",
    "of": "of",
    "edit_name": "Enter new name:",
    "edit_age": "Enter new age:",
    "edit_city": "Enter new city:",
    "edit_description": "Enter new description:",
    "gender_male": "Male",
    "gender_female": "Female",
    "gender_other": "Other",
    "looking_male": "Men",
    "looking_female": "Women",
    "looking_all": "All",
}

def get_text(key: str, language: Language, **kwargs) -> str:
    texts = TEXTS_RU if language == Language.RU else TEXTS_EN
    text = texts.get(key, key)
    if kwargs and text:
        return str(text).format(**kwargs)
    return text


def format_profile(user, language: Language) -> str:
    of_text = get_text("of", language)
    return (
        f"{user.name or 'N/A'}, {user.age or '?'} {of_text} {user.city or 'N/A'}\n\n"
        f"{user.description or ''}"
    )[:1024]
