from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple

from telegram import Update, Message
from telegram.ext import ContextTypes

from utils.lang import get_lang, T
from utils.parse_reminder import parse_delay
from utils.json_utils import safe_load_json, async_save_json
from services.openai_service import ask_openai

# Логгер модуля
logger = logging.getLogger(__name__)

# Путь к файлу и создание директории для данных
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REMINDERS_PATH = DATA_DIR / "reminders.json"

@dataclass
class Reminder:
    """Структура напоминания без идентификатора."""
    at: datetime
    msg: str


def parse_reminder_from_delay(
    delay: Tuple[Any, str]
) -> Optional[Reminder]:
    """
    Преобразует результат parse_delay в Reminder.

    :param delay: кортеж (datetime или int, сообщение)
    :return: Reminder с точным временем или None
    """
    time_val, msg = delay
    if isinstance(time_val, datetime):
        at = time_val
    else:
        minutes = int(time_val)
        at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return Reminder(at=at, msg=msg)


async def reply_error(message: Message, text: str) -> None:
    """
    Отправляет сообщение об ошибке пользователю и логирует событие.
    """
    try:
        await message.reply_text(text)
    except Exception:
        logger.exception("Ошибка при отправке ошибки пользователю %s", message.from_user.id)
    finally:
        logger.error("Ошибка для пользователя %s", message.from_user.id)


async def on_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Обрабатывает входящий текст:
    - Если распознаётся как напоминание: сохраняет его и подтверждает.
    - Иначе: перенаправляет в OpenAI и возвращает ответ.
    """
    message = update.message
    if not message or not message.text:
        logger.warning("on_text вызван без текста.")
        return

    user_id = update.effective_user.id
    text = message.text.strip()
    lang = get_lang(user_id)
    t = T[lang]

    # Данные из bot_data
    user_data: Dict[str, Any] = context.application.bot_data.get("user_data", {})
    user_ctx: Dict[str, Any] = context.application.bot_data.get("user_ctx", {})
    openai_client = context.application.bot_data.get("openai_client")
    reminders: Optional[List[Dict[str, Any]]] = context.application.bot_data.get("reminders")

    delay = parse_delay(text, lang)
    if delay:
        try:
            rem = parse_reminder_from_delay(delay)

            # Загружаем из файла, если в bot_data нет
            if reminders is None:
                reminders = safe_load_json(str(REMINDERS_PATH), [])

            # Добавляем новое напоминание
            reminders.append({
                "uid": user_id,
                "at": rem.at.isoformat(),
                "msg": rem.msg
            })

            # Сохраняем на диск и в bot_data
            await async_save_json(str(REMINDERS_PATH), reminders)
            context.application.bot_data["reminders"] = reminders

            # Формируем строку подтверждения
            time_val = delay[0]
            if isinstance(time_val, datetime):
                date_str = rem.at.strftime("%d.%m.%Y %H:%M")
            else:
                minutes = int(time_val)
                date_str = f"{minutes} МИН" if lang == "RU" else f"{minutes} MIN"

            await message.reply_text(
                t["rem_save"].format(d=date_str, m=rem.msg)
            )
            logger.info(
                "Добавлено напоминание user=%s: %s %s",
                user_id, rem.at.isoformat(), rem.msg
            )

        except (OSError, ValueError):
            logger.exception("Ошибка сохранения напоминания user=%s", user_id)
            await reply_error(message, t["err"])
        except Exception:
            logger.exception("Неизвестная ошибка при добавлении напоминания user=%s", user_id)
            await reply_error(message, t["err"])

    else:
        # Обрабатываем через OpenAI
        if openai_client is None:
            logger.error("OpenAI client не инициализирован.")
            await reply_error(message, t["err"])
            return

        try:
            reply = await ask_openai(
                user_id, text, user_ctx, user_data, openai_client
            )
            await message.reply_text(reply)
            logger.info("OpenAI ответ отправлен для user=%s", user_id)
        except Exception:
            logger.exception("OpenAI ошибка для user=%s", user_id)
            await reply_error(message, t["err"])

