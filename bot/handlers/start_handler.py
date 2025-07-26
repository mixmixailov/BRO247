from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение пользователю с его именем.
    """
    user = update.effective_user
    name = user.first_name if user and user.first_name else "друг"
    await update.message.reply_text(
        f"Привет, {name}! Рад тебя видеть здесь."
    )
