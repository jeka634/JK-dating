"""Фильтр нецензурной лексики и оскорблений."""

import re

BAD_WORDS = {
    "бля", "хуй", "пизд", "еба", "ёба", "ебл", "сука", "мудак",
    "гандон", "пидор", "чмо", "долбоёб", "уёбок", "шлюх",
    "fuck", "shit", "bitch", "asshole", "dick", "cunt", "bastard",
    "whore", "slut", "dumbass", "motherfucker",
}

BAD_PATTERNS = [
    r"пош[её]л\s+на\s*ху",
    r"иди\s+на\s*ху",
    r"отъеб",
    r"завал",
    r"сдохни",
    r"убейся",
    r"kill\s*yourself",
]


def contains_bad_words(text: str) -> bool:
    """Проверяет текст на наличие запрещённых слов."""
    text_lower = text.lower().replace(" ", "")

    # Проверка по словарю
    for word in BAD_WORDS:
        if word in text_lower:
            return True

    # Проверка по паттернам
    for pattern in BAD_PATTERNS:
        if re.search(pattern, text_lower):
            return True

    return False
