import asyncio
import datetime
import logging
from typing import List, Dict, Any
from telegram.ext import Application
from utils.json_utils import safe_load_json, async_save_json
import os

REMINDERS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reminders.json")

def load_reminders() -> List[Dict[str, Any]]:
    """
    Синхронная загрузка напоминаний из файла.
    """
    return safe_load_json(REMINDERS_PATH, [])

async def reminder_loop(app: Application, reminders: List[Dict[str, Any]]):
    """
    Проверяет напоминания каждые 30 секунд, шлёт сработавшие, удаляет их и сохраняет список.
    """
    while True:
        now = datetime.datetime.now(datetime.UTC)
        due = []
        # Ищем все сработавшие напоминания
        for r in reminders:
            try:
                at = datetime.datetime.fromisoformat(r["at"])
                if at <= now:
                    due.append(r)
            except Exception as e:
                logging.error(f"Ошибка парсинга даты в напоминании {r}: {e}")

        # Шлём напоминания
        for r in due:
            try:
                await app.bot.send_message(chat_id=r["uid"], text=f"⏰ {r['msg']}")
                logging.info(f"Напоминание отправлено (uid={r['uid']}): {r['msg']}")
            except Exception as e:
                logging.error(f"Ошибка при отправке напоминания (uid={r['uid']}): {e}")

        # Удаляем сработавшие и сохраняем только если что-то поменялось
        if due:
            before = len(reminders)
            reminders[:] = [r for r in reminders if r not in due]
            try:
                await async_save_json(REMINDERS_PATH, reminders)
                logging.info(f"Удалено и сохранено {len(due)} напоминаний. Осталось: {len(reminders)}.")
            except Exception as e:
                logging.error(f"Ошибка при сохранении reminders.json: {e}")

        await asyncio.sleep(30)
