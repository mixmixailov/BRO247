import os
import json
import logging
import aiofiles

def safe_load_json(path: str, default):
    """
    Синхронно загружает JSON-файл.
    Если файл не существует или повреждён — возвращает default и пишет ошибку в лог.
    """
    if not os.path.exists(path):
        logging.warning(f"Файл {path} не найден, возвращаю default.")
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при чтении JSON {path}: {e}")
        return default

async def async_save_json(path: str, data):
    """
    Асинхронно сохраняет data в JSON-файл.
    Если директория не существует — создаёт её.
    Ошибки пишет в лог, не выбрасывает.
    """
    try:
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        logging.info(f"Успешно сохранён JSON: {path}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении JSON {path}: {e}")

