"""Модуль безопасности для Telegram бота"""

import logging
import time
from typing import Dict, List, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    max_requests_per_minute: int = 20
    max_concurrent_users: int = 1000
    block_duration_minutes: int = 60
    suspicious_keywords: List[str] = None
    allowed_commands: List[str] = None


class SecurityManager:
    """Менеджер безопасности для Telegram бота"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.request_counts = defaultdict(deque)  # user_id -> list of timestamps
        self.blocked_users: Set[int] = set()
        self.suspicious_activity: Dict[int, int] = defaultdict(int)  # user_id -> suspicious_count
        self.active_users: Set[int] = set()
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Проверка, заблокирован ли пользователь"""
        return user_id in self.blocked_users
    
    def check_rate_limit(self, user_id: int) -> bool:
        """Проверка лимита запросов"""
        now = time.time()
        user_requests = self.request_counts[user_id]
        
        # Удаление старых запросов (старше минуты)
        while user_requests and now - user_requests[0] > 60:
            user_requests.popleft()
        
        # Проверка лимита
        if len(user_requests) >= self.config.max_requests_per_minute:
            self.block_user(user_id)
            logger.warning(f"Пользователь {user_id} заблокирован за превышение лимита запросов")
            return False
        
        # Добавление текущего запроса
        user_requests.append(now)
        return True
    
    def check_concurrent_users(self) -> bool:
        """Проверка лимита одновременных пользователей"""
        return len(self.active_users) < self.config.max_concurrent_users
    
    def block_user(self, user_id: int):
        """Блокировка пользователя"""
        self.blocked_users.add(user_id)
        logger.warning(f"Пользователь {user_id} заблокирован")
    
    def unblock_user(self, user_id: int):
        """Разблокировка пользователя"""
        self.blocked_users.discard(user_id)
        logger.info(f"Пользователь {user_id} разблокирован")
    
    def check_suspicious_activity(self, user_id: int, message: str) -> bool:
        """Проверка подозрительной активности"""
        if not self.config.suspicious_keywords:
            return True
        
        message_lower = message.lower()
        suspicious_count = 0
        
        for keyword in self.config.suspicious_keywords:
            if keyword.lower() in message_lower:
                suspicious_count += 1
        
        if suspicious_count > 0:
            self.suspicious_activity[user_id] += suspicious_count
            logger.warning(f"Подозрительная активность пользователя {user_id}: {suspicious_count} совпадений")
            
            if self.suspicious_activity[user_id] > 5:
                self.block_user(user_id)
                return False
        
        return True
    
    def register_user(self, user_id: int):
        """Регистрация активного пользователя"""
        self.active_users.add(user_id)
    
    def unregister_user(self, user_id: int):
        """Удаление пользователя из активных"""
        self.active_users.discard(user_id)
        self.request_counts.pop(user_id, None)
        self.suspicious_activity.pop(user_id, None)


# Глобальный менеджер безопасности
security_manager = SecurityManager()


def security_check(func):
    """Декоратор для проверки безопасности"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        message = update.message.text if update.message else ""
        
        # Проверка блокировки
        if security_manager.is_user_blocked(user_id):
            await update.message.reply_text("Вы были заблокированы за нарушение правил использования бота.")
            return
        
        # Проверка лимита запросов
        if not security_manager.check_rate_limit(user_id):
            await update.message.reply_text("Превышен лимит запросов. Попробуйте позже.")
            return
        
        # Проверка подозрительной активности
        if not security_manager.check_suspicious_activity(user_id, message):
            await update.message.reply_text("Ваш аккаунт заблокирован за подозрительную активность.")
            return
        
        # Регистрация пользователя
        security_manager.register_user(user_id)
        
        try:
            return await func(update, context, *args, **kwargs)
        finally:
            # Всегда удаляем пользователя из активных после обработки
            security_manager.unregister_user(user_id)
    
    return wrapper


def validate_input(pattern: str = None, max_length: int = None):
    """Декоратор для валидации входных данных"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            message = update.message.text if update.message else ""
            
            # Проверка длины сообщения
            if max_length and len(message) > max_length:
                await update.message.reply_text(f"Сообщение слишком длинное. Максимум {max_length} символов.")
                return
            
            # Проверка по шаблону (если указан)
            if pattern:
                import re
                if not re.match(pattern, message):
                    await update.message.reply_text("Неверный формат данных.")
                    return
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


# Список подозрительных ключевых слов
SUSPICIOUS_KEYWORDS = [
    'hack', 'exploit', 'sql', 'inject', 'botnet', 'ddos',
    'spam', 'phishing', 'malware', 'virus', 'trojan'
]

# Разрешенные команды
ALLOWED_COMMANDS = [
    '/start', '/help', '/search', '/evaluate', '/analytics', '/settings'
]


def init_security_manager():
    """Инициализация менеджера безопасности"""
    global security_manager
    security_manager = SecurityManager(SecurityConfig(
        max_requests_per_minute=20,
        max_concurrent_users=1000,
        block_duration_minutes=60,
        suspicious_keywords=SUSPICIOUS_KEYWORDS,
        allowed_commands=ALLOWED_COMMANDS
    ))
    logger.info("Менеджер безопасности инициализирован")


# Функции для администраторов
async def admin_block_user(user_id: int, reason: str = "Нарушение правил"):
    """Блокировка пользователя администратором"""
    security_manager.block_user(user_id)
    logger.warning(f"Пользователь {user_id} заблокирован администратором. Причина: {reason}")


async def admin_unblock_user(user_id: int):
    """Разблокировка пользователя администратором"""
    security_manager.unblock_user(user_id)
    logger.info(f"Пользователь {user_id} разблокирован администратором")


async def get_security_stats() -> Dict[str, int]:
    """Получение статистики безопасности"""
    return {
        'blocked_users': len(security_manager.blocked_users),
        'active_users': len(security_manager.active_users),
        'suspicious_users': len([u for u, count in security_manager.suspicious_activity.items() if count > 0])
    }