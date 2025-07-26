# handlers/reminders.py

import logging
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

from utils.lang import get_lang, T
from utils.json_utils import safe_load_json, async_save_json

# Логгер модуля
logger = logging.getLogger(__name__)

# Пути
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REMINDERS_FILE = DATA_DIR / "reminders.json"


@dataclass
class Reminder:
    """Структура напоминания."""
    id: str
    uid: int
    at: datetime.datetime
    msg: str


def _load_reminders() -> List[Reminder]:
    """
    Загрузить все напоминания из файла.
    Игнорирует некорректные записи с ошибками парсинга.
    """
    raw = safe_load_json(str(REMINDERS_FILE), [])
    result: List[Reminder] = []
    for item in raw:
        try:
            rem = Reminder(
                id=item["id"],
                uid=item["uid"],
                at=datetime.datetime.fromisoformat(item["at"]),
                msg=item["msg"],
            )
            result.append(rem)
        except Exception:
            logger.exception("Невозможно распарсить запись напоминания: %s", item)
    return result


async def _save_reminders(reminders: List[Reminder]) -> None:
    """
    Асинхронно сохранить список напоминаний в файл.
    """
    data = [asdict(r) for r in reminders]
    try:
        await async_save_json(str(REMINDERS_FILE), data)
    except OSError:
        logger.exception("Ошибка записи файла напоминаний")


def _get_user_reminders(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> List[Reminder]:
    """
    Получить список напоминаний для пользователя:
    из cache в bot_data или загрузить из файла.
    """
    cache = context.application.bot_data.get("reminders")
    if cache is None:
        cache = _load_reminders()
        context.application.bot_data["reminders"] = cache
    # Фильтр по пользователю
    return [r for r in cache if r.uid == user_id]


def _format_reminders(reminders: List[Reminder], lang: str) -> str:
    """
    Сформировать удобочитаемый текст списка напоминаний.
    """
    lines = []
    for r in reminders:
        dt = r.at.strftime("%d.%m.%Y %H:%M")
        lines.append(f"{dt} — {r.msg}")
    return T[lang]["reminders_list"] + "\n" + "\n".join(lines)


def _build_keyboard(reminders: List[Reminder], lang: str) -> InlineKeyboardMarkup:
    """
    Построить inline-клавиатуру с кнопками удаления.
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=T[lang]["delete_button"],
                callback_data=f"delete_reminder:{r.id}"
            )
        ]
        for r in reminders
    ]
    return InlineKeyboardMarkup(buttons)


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Хендлер /reminders:
    показывает пользователю список его напоминаний с кнопками «Удалить».
    """
    user_id = update.effective_user.id
    lang = get_lang(user_id)

    try:
        user_rems = _get_user_reminders(context, user_id)
        if not user_rems:
            await update.message.reply_text(T[lang]["no_reminders"])
            return

        text = _format_reminders(user_rems, lang)
        keyboard = _build_keyboard(user_rems, lang)
        await update.message.reply_text(text, reply_markup=keyboard)

    except Exception:
        logger.exception("Ошибка в reminders_command для пользователя %s", user_id)
        await update.message.reply_text(T[lang]["err"])


async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Callback-хендлер для удаления напоминания по нажатию кнопки.
    """
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_lang(user_id)

    parts = query.data.split(":", 1)
    if len(parts) != 2:
        logger.error("Неверный callback_data: %s", query.data)
        await query.message.reply_text(T[lang]["err"])
        return

    rem_id = parts[1]

    try:
        all_rems: List[Reminder] = context.application.bot_data.get("reminders") or _load_reminders()
        new_rems = [
            r for r in all_rems
            if not (r.uid == user_id and r.id == rem_id)
        ]
        if len(new_rems) == len(all_rems):
            # ничего не удалилось
            await query.message.reply_text(T[lang]["err"])
            return

        # Сохраняем обновлённый список
        context.application.bot_data["reminders"] = new_rems
        await _save_reminders(new_rems)

        await query.message.reply_text(T[lang]["reminder_deleted"])
        logger.info("Удалено напоминание %s для пользователя %s", rem_id, user_id)

    except Exception:
        logger.exception("Ошибка удаления напоминания %s для %s", rem_id, user_id)
        await query.message.reply_text(T[lang]["err"])


def setup(application: Application) -> None:
    """
    Регистрация хендлеров модуля напоминаний.
    """
    application.add_handler(CommandHandler("reminders", reminders_command))
    application.add_handler(
        CallbackQueryHandler(delete_callback, pattern=r"^delete_reminder:")
    )
