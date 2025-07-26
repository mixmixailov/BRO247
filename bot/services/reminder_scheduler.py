from pathlib import Path
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.ext import Application, ContextTypes, JobQueue, Job

from utils.lang import get_lang, T
from utils.json_utils import safe_load_json, async_save_json

# Логгер модуля
logger = logging.getLogger(__name__)

# Путь к файлу напоминаний и создание директории
REMINDERS_FILE = Path(__file__).parent.parent / "data" / "reminders.json"
REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class Reminder:
    id: str
    uid: int
    at: datetime
    msg: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        return cls(
            id=data["id"],
            uid=data["uid"],
            at=datetime.fromisoformat(data["at"]),
            msg=data["msg"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "uid": self.uid,
            "at": self.at.isoformat(),
            "msg": self.msg,
        }


def load_reminders() -> List[Reminder]:
    """
    Загрузить все напоминания из файла. Возвращает список Reminder или пустой список при ошибке.
    """
    try:
        raw = safe_load_json(str(REMINDERS_FILE), [])
        if not isinstance(raw, list):
            logger.error("Неверный формат reminders.json, ожидается список")
            return []
        reminders: List[Reminder] = []
        for item in raw:
            try:
                reminders.append(Reminder.from_dict(item))
            except Exception:
                logger.exception("Не удалось распарсить напоминание: %s", item)
        return reminders
    except Exception:
        logger.exception("Ошибка при загрузке reminders.json")
        return []

async def save_reminders(reminders: List[Reminder]) -> bool:
    """
    Асинхронно сохранить напоминания в файл. Возвращает True при успехе.
    """
    try:
        data = [r.to_dict() for r in reminders]
        REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        await async_save_json(str(REMINDERS_FILE), data)
        return True
    except (OSError, ValueError):
        logger.exception("Ошибка при сохранении reminders.json")
        return False

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправить одно напоминание и удалить его из хранилища.
    """
    reminder: Reminder = context.job.data["reminder"]
    lang = get_lang(reminder.uid)
    text = T[lang]["reminder_alert"].format(m=reminder.msg)

    try:
        await context.bot.send_message(chat_id=reminder.uid, text=text)
        logger.info("Отправлено напоминание %s для user=%s", reminder.id, reminder.uid)
    except Exception:
        logger.exception("Ошибка отправки напоминания %s для %s", reminder.id, reminder.uid)

    # Удаляем отправленное напоминание
    reminders = load_reminders()
    reminders = [r for r in reminders if r.id != reminder.id]
    context.application.bot_data["reminders"] = reminders
    await save_reminders(reminders)


def schedule_reminder(
    reminder: Reminder,
    job_queue: JobQueue
) -> Optional[Job]:
    """
    Запланировать одно напоминание. Возвращает Job или None.
    """
    delay = (reminder.at - datetime.now(timezone.utc)).total_seconds()
    if delay <= 0:
        logger.info("Пропущено устаревшее напоминание %s", reminder.id)
        return None
    try:
        job = job_queue.run_once(
            send_reminder,
            when=delay,
            chat_id=reminder.uid,
            data={"reminder": reminder},
            name=f"reminder_{reminder.id}"
        )
        logger.info("Запланировано напоминание %s на %s", reminder.id, reminder.at)
        return job
    except Exception:
        logger.exception("Не удалось запланировать напоминание %s", reminder.id)
        return None

async def _startup(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    При запуске бота: загружает напоминания, удаляет просроченные, сохраняет и планирует оставшиеся.
    """
    application: Application = context.application
    job_queue: JobQueue = application.job_queue

    all_rems = load_reminders()
    # Фильтруем будущие
    now = datetime.now(timezone.utc)
    valid = [r for r in all_rems if r.at > now]

    # Если были просроченные — сохраняем
    if len(valid) < len(all_rems):
        application.bot_data["reminders"] = valid
        await save_reminders(valid)
    else:
        application.bot_data["reminders"] = valid

    for rem in valid:
        schedule_reminder(rem, job_queue)


def setup(application: Application) -> None:
    """
    Регистрация планировщика напоминаний при старте.
    """
    # Запускаем _startup сразу после старта
    application.job_queue.run_once(_startup, when=0)
    logger.info("Инициализирован планировщик напоминаний при старте бота")
