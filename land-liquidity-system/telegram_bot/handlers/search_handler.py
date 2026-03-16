"""Обработчик поиска участков"""

from typing import Dict, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from services.api_client import APIClient
from utils.validators import validate_cadastral_number
from utils.formatters import format_parcel_info
from keyboards.search_keyboard import get_search_keyboard


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /search"""
    await update.message.reply_text(
        "Введите кадастровый номер участка для поиска.\n"
        "Формат: 78:12:0000101:123"
    )
    context.user_data['awaiting_cadastral_number'] = True


async def handle_cadastral_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенного кадастрового номера"""
    user_id = update.effective_user.id
    message = update.message.text.strip()
    
    # Сброс флага ожидания
    context.user_data['awaiting_cadastral_number'] = False
    
    # Валидация кадастрового номера
    if not validate_cadastral_number(message):
        await update.message.reply_text(
            "❌ Неверный формат кадастрового номера.\n"
            "Введите номер в формате: 78:12:0000101:123"
        )
        return
    
    # Поиск участка через API
    api_client = APIClient()
    try:
        parcel_data = await api_client.search_parcel(message)
        
        if parcel_data:
            # Форматирование информации об участке
            info_text = format_parcel_info(parcel_data)
            
            # Клавиатура действий с участком
            keyboard = get_search_keyboard(message)
            
            await update.message.reply_text(
                info_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f"❌ Участок с кадастровым номером {message} не найден."
            )
    
    except Exception as e:
        logger.error(f"Ошибка при поиске участка: {e}")
        await update.message.reply_text(
            "Произошла ошибка при поиске участка. Пожалуйста, попробуйте позже."
        )


async def search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-запросов от кнопок поиска"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    cadastral_number = data.split('_')[1]  # search_{cadastral_number}
    
    if data.startswith('search_evaluate_'):
        # Оценить ликвидность участка
        await _initiate_evaluation(update, context, cadastral_number)
    elif data.startswith('search_analytics_'):
        # Показать аналитику по участку
        await _show_analytics(update, context, cadastral_number)
    elif data.startswith('search_more_'):
        # Показать дополнительную информацию
        await _show_additional_info(update, context, cadastral_number)


async def _initiate_evaluation(update: Update, context: ContextTypes.DEFAULT_TYPE, cadastral_number: str):
    """Инициация оценки ликвидности"""
    await update.callback_query.message.reply_text(
        f"Начинаем оценку ликвидности для участка {cadastral_number}.\n"
        "Пожалуйста, укажите площадь участка в квадратных метрах."
    )
    context.user_data['awaiting_evaluation_data'] = True
    context.user_data['evaluation_cadastral_number'] = cadastral_number
    context.user_data['evaluation_step'] = 'area'


async def _show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE, cadastral_number: str):
    """Показать аналитику по участку"""
    api_client = APIClient()
    try:
        analytics_data = await api_client.get_parcel_analytics(cadastral_number)
        
        if analytics_data:
            analytics_text = format_analytics_info(analytics_data)
            await update.callback_query.message.reply_text(
                analytics_text,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.message.reply_text(
                "Для этого участка нет доступной аналитики."
            )
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики: {e}")
        await update.callback_query.message.reply_text(
            "Произошла ошибка при получении аналитики. Пожалуйста, попробуйте позже."
        )


async def _show_additional_info(update: Update, context: ContextTypes.DEFAULT_TYPE, cadastral_number: str):
    """Показать дополнительную информацию об участке"""
    # Здесь можно добавить логику для показа дополнительной информации
    await update.callback_query.message.reply_text(
        f"Дополнительная информация для участка {cadastral_number}.\n"
        "Эта функция находится в разработке."
    )


def format_analytics_info(analytics_data: Dict[str, Any]) -> str:
    """Форматирование информации об аналитике"""
    # Реализация форматирования аналитики
    return f"Аналитика для участка: {analytics_data.get('cadastral_number', 'N/A')}"