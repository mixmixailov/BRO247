import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import aiofiles

# Асинхронный лок для безопасности при записи
_lock = asyncio.Lock()

# Путь к файлу напоминаний
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REMINDERS_FILE = DATA_DIR / "reminders.json"

@dataclass
class Reminder:
    """Структура напоминания."""
    id: str
    uid: int
    at: datetime
    msg: str


def _parse_reminder(obj: dict) -> Reminder:
    """Преобразует словарь в объект Reminder."""
    return Reminder(
        id=obj["id"],
        uid=obj["uid"],
        at=datetime.fromisoformat(obj["at"]),
        msg=obj["msg"]
    )


def load_reminders() -> List[Reminder]:
    """
    Загружает список напоминаний из JSON-файла.
    Если файл отсутствует или некорректен, возвращает пустой список.
    """
    if not REMINDERS_FILE.exists():
        return []
    try:
        raw = REMINDERS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        return [_parse_reminder(item) for item in data]
    except (json.JSONDecodeError, IOError):
        return []


async def save_reminders(reminders: List[Reminder]) -> bool:
    """
    Сохраняет список напоминаний в JSON-файл асинхронно.
    Возвращает True при успешной записи.
    """
    async with _lock:
        try:
            data = [
                {"id": r.id, "uid": r.uid, "at": r.at.isoformat(), "msg": r.msg}
                for r in reminders
            ]
            async with aiofiles.open(REMINDERS_FILE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        except Exception:
            return False


async def add_reminder(reminder: Reminder) -> bool:
    """
    Добавляет новое напоминание в хранилище.
    Загружает существующие, добавляет, сохраняет.
    """
    reminders = load_reminders()
    reminders.append(reminder)
    return await save_reminders(reminders)
