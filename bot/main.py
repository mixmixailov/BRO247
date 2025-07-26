import os
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, Request
from telegram import Update

from bot import create_bot

# Загрузка переменных окружения
load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Глобальный объект приложения Telegram
application = None

# Инициализация FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """
    Создаёт Telegram Application, инициализирует его,
    запускает и устанавливает webhook.
    """
    global application
    application = await create_bot()
    # Инициализация и запуск приложения
    await application.initialize()
    await application.start()
    # Установка webhook
    await application.bot.set_webhook(url=WEBHOOK_URL)

@app.post("/webhook")
async def webhook(request: Request):
    """
    Обрабатывает входящие запросы от Telegram по webhook.
    Парсит Update и добавляет в очередь обработки.
    """
    global application
    if application is None:
        return {"error": "Application not initialized"}
    # Получаем JSON тела запроса
    data = await request.json()
    # Создаём объект Update
    update = Update.de_json(data, application.bot)
    # Добавляем в очередь обновлений
    await application.update_queue.put(update)
    return {"ok": True}
