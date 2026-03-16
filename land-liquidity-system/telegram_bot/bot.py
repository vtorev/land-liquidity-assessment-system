"""Основной файл Telegram бота"""

import logging
import asyncio
from typing import Dict, Any
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram import Update, BotCommand

from config import Config
from handlers import (
    start_handler,
    search_handler,
    evaluate_handler,
    analytics_handler,
    settings_handler
)
from services.notification_service import NotificationService
from utils.logger import setup_logger

# Настройка логирования
setup_logger()
logger = logging.getLogger(__name__)

class LandLiquidityBot:
    """Основной класс Telegram бота для оценки ликвидности земельных участков"""
    
    def __init__(self):
        """Инициализация бота"""
        Config.validate()
        self.config = Config.get_bot_config()
        self.notification_service = None
        
        # Создание приложения
        self.app = Application.builder().token(self.config.token).build()
        
        # Регистрация обработчиков
        self._setup_handlers()
        self._setup_commands()
        
        # Регистрация обработчиков ошибок
        self.app.add_error_handler(self.error_handler)
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        # Команды
        self.app.add_handler(CommandHandler("start", start_handler.start))
        self.app.add_handler(CommandHandler("help", start_handler.help_command))
        self.app.add_handler(CommandHandler("search", search_handler.search_command))
        self.app.add_handler(CommandHandler("evaluate", evaluate_handler.evaluate_command))
        self.app.add_handler(CommandHandler("analytics", analytics_handler.analytics_command))
        self.app.add_handler(CommandHandler("settings", settings_handler.settings_command))
        
        # Обработчики сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        # Обработчики callback-запросов
        self.app.add_handler(CallbackQueryHandler(search_handler.search_callback, pattern="^search_"))
        self.app.add_handler(CallbackQueryHandler(evaluate_handler.evaluate_callback, pattern="^evaluate_"))
        self.app.add_handler(CallbackQueryHandler(analytics_handler.analytics_callback, pattern="^analytics_"))
        self.app.add_handler(CallbackQueryHandler(settings_handler.settings_callback, pattern="^settings_"))
    
    def _setup_commands(self):
        """Настройка команд бота"""
        commands = [
            BotCommand("start", "Начать работу с ботом"),
            BotCommand("help", "Помощь и инструкции"),
            BotCommand("search", "Поиск участка по кадастровому номеру"),
            BotCommand("evaluate", "Оценить ликвидность участка"),
            BotCommand("analytics", "Рыночная аналитика"),
            BotCommand("settings", "Настройки уведомлений"),
        ]
        self.app.bot.set_my_commands(commands)
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Общий обработчик сообщений"""
        user_id = update.effective_user.id
        message = update.message.text
        
        logger.info(f"Получено сообщение от пользователя {user_id}: {message}")
        
        # Проверка состояния пользователя
        if context.user_data.get('awaiting_cadastral_number'):
            await search_handler.handle_cadastral_number(update, context)
        elif context.user_data.get('awaiting_evaluation_data'):
            await evaluate_handler.handle_evaluation_data(update, context)
        else:
            # Отправка приветственного сообщения
            await start_handler.start(update, context)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка при обработке обновления: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка. Пожалуйста, попробуйте позже."
            )
    
    async def setup_notification_service(self):
        """Настройка сервиса уведомлений"""
        if Config.get_notification_config().enabled:
            self.notification_service = NotificationService(self.app.bot)
            # Запуск фоновой задачи для уведомлений
            self.app.job_queue.run_repeating(
                self.notification_service.check_notifications,
                interval=Config.get_notification_config().check_interval,
                first=10
            )
            logger.info("Сервис уведомлений запущен")
    
    async def start(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        
        # Настройка уведомлений
        await self.setup_notification_service()
        
        # Запуск бота
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        logger.info("Telegram бот запущен и готов к работе")
    
    async def stop(self):
        """Остановка бота"""
        logger.info("Остановка Telegram бота...")
        
        if self.notification_service:
            self.notification_service.stop()
        
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        
        logger.info("Telegram бот остановлен")


async def main():
    """Главная функция запуска бота"""
    bot = LandLiquidityBot()
    
    try:
        await bot.start()
        # Ожидание завершения (бот работает в фоновом режиме)
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())