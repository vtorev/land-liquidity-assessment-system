# Dockerfile для Telegram бота

FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бота
COPY . .

# Создание директории для логов
RUN mkdir -p logs

# Запуск бота
CMD ["python", "-m", "telegram_bot.bot"]