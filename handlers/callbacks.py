import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.lang import T, get_lang, get_keyboard
from utils.json_utils import safe_load_json, async_save_json

USER_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user_data.json")

def _load_user_data():
    return safe_load_json(USER_JSON_PATH, {})

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    sid = str(user_id)

    # Всегда обновляем user_data из файла
    user_data = _load_user_data()
    lang = get_lang(user_id)
    t = T[lang]

    try:
        if query.data == "lang":
            # Кнопки RU/EN (🌐 Язык)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_RU"),
                 InlineKeyboardButton("🇬🇧 English", callback_data="lang_EN")]
            ])
            await query.message.reply_text("🌐 Выбери язык | Choose language:", reply_markup=kb)

        elif query.data.startswith("lang_"):
            user_data.setdefault(sid, {})["language"] = query.data.split("_")[1]
            await async_save_json(USER_JSON_PATH, user_data)
            await query.edit_message_text(t["lang_set"], reply_markup=get_keyboard(user_data[sid].get("language", "RU")))

        elif query.data == "style":
            kb_s = [
                [InlineKeyboardButton("🧢 Street", callback_data="s_street")],
                [InlineKeyboardButton("🧘 Psychologist", callback_data="s_psych")],
                [InlineKeyboardButton("🧑‍💼 Coach", callback_data="s_coach")]
            ]
            await query.message.reply_text(t["choose_style"], reply_markup=InlineKeyboardMarkup(kb_s))

        elif query.data.startswith("s_"):
            user_data.setdefault(sid, {})["style"] = query.data.split("_")[1]
            await async_save_json(USER_JSON_PATH, user_data)
            await query.message.reply_text(t["style_ok"])

        elif query.data == "gender":
            kb_g = [
                [InlineKeyboardButton("♂️ Male", callback_data="g_male"),
                 InlineKeyboardButton("♀️ Female", callback_data="g_female"),
                 InlineKeyboardButton("🏳️‍🌈 Skip", callback_data="g_skip")]
            ]
            await query.message.reply_text(t["q_gen"], reply_markup=InlineKeyboardMarkup(kb_g))

        elif query.data.startswith("g_"):
            g = query.data.split("_")[1]
            if g == "skip":
                user_data.setdefault(sid, {}).pop("gender", None)
                await query.message.reply_text(t["reset"])
            else:
                user_data.setdefault(sid, {})["gender"] = "female" if g == "female" else "male"
                await query.message.reply_text(t["saved"].format(t[g]))
            await async_save_json(USER_JSON_PATH, user_data)

        elif query.data == "prof":
            d = user_data.get(sid, {})
            prof_lines = [
                f"{t['lang']}: {d.get('language', '-')}",
                f"{t['style']}: {d.get('style', '-')}",
                f"{t['gen']}: {t.get(d.get('gender'), '-') if d.get('gender') else '-'}"
            ]
            await query.message.reply_text("🧑‍💼 Профиль:\n" + "\n".join(prof_lines))

        elif query.data == "clear":
            user_data.pop(sid, None)
            await async_save_json(USER_JSON_PATH, user_data)
            await query.message.reply_text("🗑️ Данные профиля удалены.")

        else:
            await query.message.reply_text("Неизвестная команда.")
        
        logging.info(f"Callback обработан: user_id={user_id}, data={query.data}")

    except Exception as e:
        logging.error(f"Ошибка в on_callback user={user_id}: {e}")
        await query.message.reply_text("Произошла ошибка. Попробуй ещё раз.")
