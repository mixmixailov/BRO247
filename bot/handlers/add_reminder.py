from pathlib import Path
import json
from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.lang import get_lang, T
from utils.parse_reminder import parse_delay
from utils.json_utils import async_save_json, safe_load_json

# Логгер модуля
logger = logging.getLogger(__name__)

# Пути
REMINDERS_FILE = Path(__file__).parent.parent / "data" / "reminders.json"
# Убедимся, что директория существует
REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class Reminder:
    """Структура напоминания."""
    id: str
    uid: int
    at: datetime
    msg: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "uid": self.uid,
            "at": self.at.isoformat(),
            "msg": self.msg,
        }


def load_reminders() -> List[Dict[str, Any]]:
    """
    Загрузить список напоминаний из файла.
    Возвращает пустой список при ошибках чтения или парсинга.
    """
    try:
        data = safe_load_json(str(REMINDERS_FILE), [])
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        logger.exception("Ошибка чтения reminders.json")
        return []


async def save_reminders(reminders: List[Dict[str, Any]]) -> bool:
    """
    Асинхронно сохранить список напоминаний в файл.
    Возвращает True при успехе, иначе False.
    """
    try:
        REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        await async_save_json(str(REMINDERS_FILE), reminders)
        return True
    except (OSError, ValueError):
        logger.exception("Ошибка записи reminders.json")
        return False


async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Хендлер добавления напоминания через /addreminder.
    Пример: /addreminder через 10 минут купить хлеб
    """
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(T[lang]["reminder_parse_error"])
        logger.info("Пустой текст у /addreminder user %s", user_id)
        return

    parsed = parse_delay(text, lang)
    if not parsed:
        await update.message.reply_text(T[lang]["reminder_parse_error"])
        logger.info("Не распознано напоминание: '%s' user %s", text, user_id)
        return

    # Определяем время напоминания
    if isinstance(parsed[0], datetime):
        at = parsed[0]
    else:
        at = datetime.now(timezone.utc) + timedelta(minutes=int(parsed[0]))
    msg = parsed[1].strip()

    reminder = Reminder(
        id=str(uuid4()),
        uid=user_id,
        at=at,
        msg=msg
    )

    # Загружаем или инициализируем кеш
    reminders: List[Dict[str, Any]] = context.application.bot_data.setdefault(
        "reminders", load_reminders()
    )
    reminders.append(reminder.to_dict())

    # Сохраняем напоминания
    success = await save_reminders(reminders)
    if success:
        date_str = at.strftime("%d.%m.%Y %H:%M")
        await update.message.reply_text(T[lang]["rem_save"].format(d=date_str, m=msg))
        logger.info("Добавлено напоминание user %s: %s %s", user_id, date_str, msg)
    else:
        await update.message.reply_text(T[lang]["err"])
        logger.error("Не удалось сохранить напоминание user %s: %s", user_id, reminder)


def setup(application: Application) -> None:
    """
    Регистрирует хендлер /addreminder
    """
    application.add_handler(CommandHandler("addreminder", add_reminder))
