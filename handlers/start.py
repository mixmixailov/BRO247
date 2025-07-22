import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

from utils.lang import get_lang, get_keyboard, T

# Логгер модуля
logger = logging.getLogger(__name__)

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Хендлер команды /start: присылает приветственное сообщение и основное меню.
    """
    # Проверяем, есть ли пользователь
    if not update.effective_user:
        logger.error("Received /start without effective_user")
        return

    user_id = update.effective_user.id
    lang = get_lang(user_id)
    text = T[lang]["welcome"]
    keyboard = get_keyboard(lang)

    try:
        # Пытаемся отправить через message.reply_text
        if update.message:
            await update.message.reply_text(text, reply_markup=keyboard)
        else:
            # fallback — отправляем напрямую ботом
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard
            )
        logger.info("Sent /start to user %s (lang=%s)", user_id, lang)
    except Exception:
        logger.exception("Error handling /start for user %s", user_id)
        # Отправляем общую ошибку пользователю
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=T[lang]["err"]
            )
        except Exception:
            logger.exception("Failed to send error message for /start to user %s", user_id)


def setup(application: Application) -> None:
    """
    Регистрация хендлера команды /start.
    """
    application.add_handler(CommandHandler("start", start))
