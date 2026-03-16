"""Обработчик команды /start и помощи"""

from typing import Dict, Any
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from services.api_client import APIClient
from keyboards.main_menu import get_main_menu_keyboard
from utils.formatters import format_welcome_message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    # Приветственное сообщение
    welcome_text = format_welcome_message(user.first_name)
    
    # Клавиатура главного меню
    keyboard = get_main_menu_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    # Сохранение пользователя в базе данных (если нужно)
    await _register_user(user_id, user.username, user.first_name, user.last_name)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
<b>Помощь по использованию бота</b>

Доступные команды:
• /start - Начать работу с ботом
• /help - Показать эту помощь
• /search - Поиск участка по кадастровому номеру
• /evaluate - Оценить ликвидность участка
• /analytics - Рыночная аналитика
• /settings - Настройки уведомлений

<b>Поиск участка:</b>
Введите команду /search и следуйте инструкциям.
Введите кадастровый номер в формате: 78:12:0000101:123

<b>Оценка ликвидности:</b>
Введите команду /evaluate и следуйте инструкциям.
Бот запросит необходимые данные для оценки.

<b>Рыночная аналитика:</b>
Введите команду /analytics для получения рыночной информации.

<b>Настройки уведомлений:</b>
Введите команду /settings для настройки уведомлений о изменениях.

Если возникли вопросы, обратитесь в поддержку.
    """
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def _register_user(user_id: int, username: str, first_name: str, last_name: str):
    """Регистрация пользователя в базе данных"""
    # Здесь можно добавить логику регистрации пользователя
    # Например, сохранение в базу данных для статистики и уведомлений
    pass