import os
import logging
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Строго требуемые переменные
REQUIRED_VARS = [
    "TELEGRAM_TOKEN",
    "OPENAI_API_KEY",
    "WEBHOOK_HOST",
]

# Проверка наличия всех переменных
missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    raise RuntimeError(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing)}")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")

# Логирование: INFO уровень, стандартный вывод
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# Можно добавить свою функцию логирования, если надо
logger = logging.getLogger(__name__)
logger.info("Конфиг загружен успешно: TELEGRAM_TOKEN, OPENAI_API_KEY, WEBHOOK_HOST")
