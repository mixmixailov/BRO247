FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект и .env
COPY . .

# Запуск приложения
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
