from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils.json_utils import safe_load_json
import os

# Путь к данным
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USER_JSON_PATH = os.path.join(DATA_DIR, "user_data.json")

# Грузим user_data (если нужен live-режим — вынеси в функцию)
user_data = safe_load_json(USER_JSON_PATH, {})

T = {
    "RU": {
        "lang": "🌐 Язык", "style": "🎭 Стиль", "rem": "⏰ Напоминание", "gen": "🧬 Пол", "prof": "🧠 Профиль", "clr": "🧹 Сброс",
        "q_gen": "Кто ты по полу?", "saved": "Запомнил! Ты {}.", "reset": "Пол сброшен.",
        "male": "мужчина", "female": "женщина", "skip": "Не указывать",
        "lang_set": "Язык установлен ✅", "welcome": "👋 Привет! Я Bro 24/7 — всегда на связи.",
        "rem_fmt": "Формат: 'через 10мин ...' / 'через 2 часа ...'", "rem_bad": "Не понял формат.",
        "rem_save": "⏰ Напомню через {d}: {m}", "style_ok": "Стиль сохранён ✅", "cleared": "🧹 Очищено.",
        "err": "Ошибка. Попробуй ещё или /start.",
        "choose_style": "Выбери стиль общения:",
        "style_street": "🔥 Уличный бро",
        "style_psych": "🧘 Психолог",
        "style_coach": "💼 Коуч",
    },
    "EN": {
        "lang": "🌐 Language", "style": "🎭 Style", "rem": "⏰ Reminder", "gen": "🧬 Gender", "prof": "🧠 Profile", "clr": "🧹 Clear",
        "q_gen": "Your gender?", "saved": "Got it! You're {}.", "reset": "Gender cleared.",
        "male": "male", "female": "female", "skip": "Skip",
        "lang_set": "Language set ✅", "welcome": "👋 Hey! I'm Bro 24/7 — always online.",
        "rem_fmt": "Format: 'in 10min ...' / 'in 2 hours ...'", "rem_bad": "Bad format.",
        "rem_save": "⏰ I'll remind you in {d}: {m}", "style_ok": "Style saved ✅", "cleared": "🧹 Cleared.",
        "err": "Error. Try again or /start.",
        "choose_style": "Choose your style:",
        "style_street": "🔥 Street bro",
        "style_psych": "🧘 Psychologist",
        "style_coach": "💼 Coach",
    },
}

def get_lang(uid: int) -> str:
    """Вернуть код языка пользователя, default RU"""
    return user_data.get(str(uid), {}).get("language", "RU")

def get_keyboard(lang_code: str):
    """Собрать главную клавиатуру для выбранного языка"""
    t = T[lang_code]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["lang"], callback_data="lang"), InlineKeyboardButton(t["style"], callback_data="style")],
        [InlineKeyboardButton(t["rem"], callback_data="rem"), InlineKeyboardButton(t["gen"], callback_data="gender")],
        [InlineKeyboardButton(t["prof"], callback_data="prof"), InlineKeyboardButton(t["clr"], callback_data="clear")],
    ])

# Для будущего — если потребуется обновлять user_data на лету
def reload_user_data():
    global user_data
    user_data = safe_load_json(USER_JSON_PATH, {})

