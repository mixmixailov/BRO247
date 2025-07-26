import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

# Загрузка переменных окружения
load_dotenv()

# Импорт функции-обработчика /start
from bot.handlers.start_handler import start


async def create_bot() -> Application:
    """
    Создаёт и настраивает асинхронного Telegram-бота.

    Загружает токен из окружения, создаёт Application,
    регистрирует хендлер для команды /start и возвращает Application.
    """
    token = os.environ["BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    return app
