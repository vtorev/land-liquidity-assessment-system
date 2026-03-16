# Инструкция по интеграции Telegram бота для системы оценки ликвидности земельных участков

## Содержание

1. [Обзор интеграции](#обзор-интеграции)
2. [Требования и зависимости](#требования-и-зависимости)
3. [Создание Telegram бота](#создание-telegram-бота)
4. [Разработка Telegram бота](#разработка-telegram-бота)
5. [Интеграция с backend API](#интеграция-с-backend-api)
6. [Развертывание и запуск](#развертывание-и-запуск)
7. [Тестирование и отладка](#тестирование-и-отладка)
8. [Безопасность и мониторинг](#безопасность-и-мониторинг)

## Обзор интеграции

Telegram бот позволит пользователям:
- Поиск земельных участков по кадастровому номеру
- Оценка ликвидности участков
- Получение рыночной аналитики
- Получение уведомлений о изменениях
- Интерактивное взаимодействие с системой

**Архитектура:**
```
Telegram Bot → Backend API → ML Models → Database
              → Frontend (для визуализации)
```

## Требования и зависимости

### Python зависимости
```bash
# Добавить в requirements.txt
python-telegram-bot==20.7
aiohttp==3.9.1
requests==2.31.0
```

### Системные требования
- Python 3.8+
- Доступ к backend API
- HTTPS для webhook (если используется)

## Создание Telegram бота

### 1. Создание бота через BotFather
```bash
# В Telegram найдите @BotFather и выполните команды:
/newbot
# Следуйте инструкциям для создания бота
# Получите токен в формате: 123456789:ABCdefGHIjklMNOpqrsTUVwxYZ1234567890
```

### 2. Настройка бота
```bash
# Установка команд бота
/setcommands
# Введите команды:
start - Начать работу с ботом
help - Помощь и инструкции
search - Поиск участка по кадастровому номеру
evaluate - Оценить ликвидность участка
analytics - Рыночная аналитика
settings - Настройки уведомлений
```

## Разработка Telegram бота

### 1. Структура проекта
```
telegram_bot/
├── bot.py                    # Основной файл бота
├── handlers/                 # Обработчики команд
│   ├── start_handler.py
│   ├── search_handler.py
│   ├── evaluate_handler.py
│   ├── analytics_handler.py
│   └── settings_handler.py
├── services/                 # Сервисы для работы с API
│   ├── api_client.py
│   ├── data_processor.py
│   └── notification_service.py
├── keyboards/                # Клавиатуры и кнопки
│   ├── main_menu.py
│   ├── search_keyboard.py
│   └── evaluation_keyboard.py
├── utils/                    # Вспомогательные функции
│   ├── validators.py
│   ├── formatters.py
│   └── logger.py
└── config.py                 # Конфигурация
```

### 2. Конфигурация бота

<write_to_file>
<path>telegram_bot/config.py</path>
<content>"""Конфигурация Telegram бота"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class BotConfig:
    """Конфигурация Telegram бота"""
    token: str
    api_base_url: str
    api_timeout: int = 30
    max_message_length: int = 4096
    rate_limit_requests: int = 20
    rate_limit_window: int = 60

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных для хранения пользователей"""
    host: str
    port: int
    database: str
    user: str
    password: str

@dataclass
class NotificationConfig:
    """Конфигурация уведомлений"""
    enabled: bool = True
    check_interval: int = 3600  # Проверять каждые 60 минут
    max_notifications_per_day: int = 10

class Config:
    """Основной класс конфигурации"""
    
    # Telegram бот
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # База данных
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'land_liquidity_telegram')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    
    # Уведомления
    NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'True').lower() == 'true'
    NOTIFICATION_CHECK_INTERVAL = int(os.getenv('NOTIFICATION_CHECK_INTERVAL', '3600'))
    MAX_NOTIFICATIONS_PER_DAY = int(os.getenv('MAX_NOTIFICATIONS_PER_DAY', '10'))
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/telegram_bot.log')
    
    # Валидация
    @classmethod
    def validate(cls):
        """Проверка конфигурации"""
        if cls.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            raise ValueError("Необходимо установить TELEGRAM_BOT_TOKEN")
        
        if not cls.API_BASE_URL.startswith(('http://', 'https://')):
            raise ValueError("API_BASE_URL должен начинаться с http:// или https://")
    
    @classmethod
    def get_bot_config(cls) -> BotConfig:
        """Получение конфигурации бота"""
        return BotConfig(
            token=cls.BOT_TOKEN,
            api_base_url=cls.API_BASE_URL,
            api_timeout=30,
            max_message_length=4096,
            rate_limit_requests=20,
            rate_limit_window=60
        )
    
    @classmethod
    def get_db_config(cls) -> DatabaseConfig:
        """Получение конфигурации базы данных"""
        return DatabaseConfig(
            host=cls.DB_HOST,
            port=cls.DB_PORT,
            database=cls.DB_NAME,
            user=cls.DB_USER,
            password=cls.DB_PASSWORD
        )
    
    @classmethod
    def get_notification_config(cls) -> NotificationConfig:
        """Получение конфигурации уведомлений"""
        return NotificationConfig(
            enabled=cls.NOTIFICATIONS_ENABLED,
            check_interval=cls.NOTIFICATION_CHECK_INTERVAL,
            max_notifications_per_day=cls.MAX_NOTIFICATIONS_PER_DAY
        )