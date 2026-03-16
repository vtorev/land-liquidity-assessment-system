"""Настройка логирования для Telegram бота"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

# Формат логов
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FORMAT_DETAILED = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'


def setup_logger(
    name: str = 'telegram_bot',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """Настройка логгера
    
    Args:
        name: Имя логгера
        level: Уровень логирования
        log_file: Путь к файлу логов
        max_file_size: Максимальный размер файла логов
        backup_count: Количество резервных файлов
        console_output: Вывод в консоль
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Очистка существующих обработчиков
    logger.handlers.clear()
    
    # Форматтеры
    formatter = logging.Formatter(LOG_FORMAT)
    detailed_formatter = logging.Formatter(LOG_FORMAT_DETAILED)
    
    # Обработчик для файла (если указан)
    if log_file:
        # Создание директории для логов
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Ротация логов
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Предотвращение дублирования логов
    logger.propagate = False
    
    return logger


def log_execution_time(func):
    """Декоратор для логирования времени выполнения функции"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger = logging.getLogger('telegram_bot.performance')
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} выполнена за {execution_time:.2f} секунд")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} завершилась с ошибкой за {execution_time:.2f} секунд: {e}")
            raise
    
    return wrapper


def log_user_action(action: str):
    """Декоратор для логирования действий пользователя"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else 'unknown'
            username = update.effective_user.username if update.effective_user else 'unknown'
            message_text = update.message.text if update.message else 'no message'
            
            logger = logging.getLogger('telegram_bot.user_actions')
            logger.info(f"User {user_id} (@{username}) - {action}: {message_text}")
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


# Инициализация основного логгера
def init_logging():
    """Инициализация логирования"""
    import os
    from config import Config
    
    # Основной логгер
    setup_logger(
        name='telegram_bot',
        level=Config.LOG_LEVEL,
        log_file=Config.LOG_FILE,
        console_output=True
    )
    
    # Логгер для производительности
    setup_logger(
        name='telegram_bot.performance',
        level='INFO',
        log_file=Config.LOG_FILE.replace('.log', '_performance.log'),
        console_output=False
    )
    
    # Логгер для действий пользователей
    setup_logger(
        name='telegram_bot.user_actions',
        level='INFO',
        log_file=Config.LOG_FILE.replace('.log', '_user_actions.log'),
        console_output=False
    )
    
    # Логгер для безопасности
    setup_logger(
        name='telegram_bot.security',
        level='WARNING',
        log_file=Config.LOG_FILE.replace('.log', '_security.log'),
        console_output=False
    )
    
    logging.getLogger('telegram_bot').info("Логирование инициализировано")


if __name__ == "__main__":
    # Тестирование логирования
    init_logging()
    logger = logging.getLogger('telegram_bot')
    logger.info("Тестовое сообщение")
    logger.warning("Тестовое предупреждение")
    logger.error("Тестовая ошибка")