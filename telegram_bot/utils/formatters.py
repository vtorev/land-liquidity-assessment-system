"""Функции для форматирования сообщений"""

from typing import Dict, Any, Optional
from datetime import datetime


def format_welcome_message(user_name: str) -> str:
    """Форматирование приветственного сообщения"""
    return f"""
👋 Добро пожаловать, <b>{user_name}</b>!

Я - бот для оценки ликвидности земельных участков. 
С моей помощью вы можете:

🔍 <b>Найти участок</b> по кадастровому номеру
💰 <b>Оценить ликвидность</b> участка с помощью ML-моделей
📈 <b>Получить рыночную аналитику</b> и тренды цен
🔔 <b>Настроить уведомления</b> об изменениях

Для начала работы выберите действие в меню или воспользуйтесь командами:

• /search - Поиск участка
• /evaluate - Оценить ликвидность
• /analytics - Рыночная аналитика
• /settings - Настройки
• /help - Помощь

Готовы начать? 🚀
    """


def format_parcel_info(parcel_data: Dict[str, Any]) -> str:
    """Форматирование информации об участке"""
    cadastral_number = parcel_data.get('cadastral_number', 'N/A')
    address = parcel_data.get('address', 'N/A')
    area = parcel_data.get('area', 0)
    category = parcel_data.get('category', 'N/A')
    purpose = parcel_data.get('purpose', 'N/A')
    coordinates = parcel_data.get('coordinates')
    
    # Форматирование координат
    coordinates_text = ""
    if coordinates:
        lat = coordinates.get('latitude', 0)
        lon = coordinates.get('longitude', 0)
        coordinates_text = f"\n📍 Координаты: {lat:.6f}, {lon:.6f}"
    
    return f"""
<b>Информация об участке</b>

🔢 <b>Кадастровый номер:</b> {cadastral_number}
🏠 <b>Адрес:</b> {address}
📏 <b>Площадь:</b> {area:,} м²
🏷️ <b>Категория:</b> {category}
🎯 <b>Назначение:</b> {purpose}{coordinates_text}

Выберите действие:
• Оценить ликвидность
• Показать аналитику
• Подписаться на уведомления
    """.strip()


def format_evaluation_result(evaluation_result: Dict[str, Any]) -> str:
    """Форматирование результата оценки ликвидности"""
    cadastral_number = evaluation_result.get('cadastral_number', 'N/A')
    liquidity_score = evaluation_result.get('liquidity_score', 0)
    liquidity_category = evaluation_result.get('liquidity_category', 'N/A')
    predicted_price = evaluation_result.get('predicted_price')
    confidence_interval = evaluation_result.get('confidence_interval')
    
    # Определение уровня ликвидности
    if liquidity_score >= 0.7:
        level_emoji = "🟢"
        level_text = "Высокая"
    elif liquidity_score >= 0.4:
        level_emoji = "🟡"
        level_text = "Средняя"
    else:
        level_emoji = "🔴"
        level_text = "Низкая"
    
    # Форматирование цены
    price_text = ""
    if predicted_price:
        price_text = f"\n💰 <b>Прогнозируемая цена:</b> {predicted_price:,.0f} руб."
    
    # Форматирование доверительного интервала
    confidence_text = ""
    if confidence_interval:
        min_price = confidence_interval.get('min', 0)
        max_price = confidence_interval.get('max', 0)
        confidence_text = f"\n📊 <b>Доверительный интервал:</b> {min_price:,.0f} - {max_price:,.0f} руб."
    
    return f"""
<b>Результат оценки ликвидности</b>

🔢 <b>Кадастровый номер:</b> {cadastral_number}
{level_emoji} <b>Уровень ликвидности:</b> {level_text}
📈 <b>Индекс ликвидности:</b> {liquidity_score:.2f} из 1.0
🎯 <b>Категория:</b> {liquidity_category}{price_text}{confidence_text}

<i>Оценка основана на анализе рыночных данных, инфраструктуры и географических факторов.</i>
    """.strip()


def format_analytics_info(analytics_data: Dict[str, Any]) -> str:
    """Форматирование рыночной аналитики"""
    region = analytics_data.get('region', 'N/A')
    average_price = analytics_data.get('average_price', 0)
    trend = analytics_data.get('trend', 'N/A')
    comparables = analytics_data.get('comparables', [])
    
    # Форматирование тренда
    if trend == 'up':
        trend_emoji = "📈"
        trend_text = "Рост цен"
    elif trend == 'down':
        trend_emoji = "📉"
        trend_text = "Снижение цен"
    else:
        trend_emoji = "➡️"
        trend_text = "Стабильные цены"
    
    # Форматирование сравнительных данных
    comparables_text = ""
    if comparables:
        comparables_text = "\n\n<b>Сравнительные предложения:</b>\n"
        for i, comp in enumerate(comparables[:3], 1):
            comp_price = comp.get('price', 0)
            comp_area = comp.get('area', 0)
            comp_cadastral = comp.get('cadastral_number', 'N/A')
            comparables_text += f"{i}. {comp_cadastral} - {comp_price:,.0f} руб. ({comp_area} м²)\n"
    
    return f"""
<b>Рыночная аналитика</b>

🗺️ <b>Регион:</b> {region}
💰 <b>Средняя цена:</b> {average_price:,.0f} руб./м²
{trend_emoji} <b>Тренд:</b> {trend_text}{comparables_text}

<i>Данные обновляются ежедневно на основе рыночных предложений.</i>
    """.strip()


def format_notification_message(notification_data: Dict[str, Any]) -> str:
    """Форматирование сообщения уведомления"""
    cadastral_number = notification_data.get('cadastral_number', 'N/A')
    change_type = notification_data.get('change_type', 'N/A')
    change_data = notification_data.get('change_data', {})
    
    if change_type == 'price_change':
        old_price = change_data.get('old_price', 0)
        new_price = change_data.get('new_price', 0)
        change_percent = ((new_price - old_price) / old_price) * 100 if old_price > 0 else 0
        
        return f"""
🔔 <b>Изменение цены участка</b>

🔢 <b>Участок:</b> {cadastral_number}
💰 <b>Старая цена:</b> {old_price:,.0f} руб.
💵 <b>Новая цена:</b> {new_price:,.0f} руб.
📈 <b>Изменение:</b> {change_percent:+.1f}%

Проверьте актуальную информацию в приложении.
        """.strip()
    
    elif change_type == 'liquidity_change':
        old_score = change_data.get('old_score', 0)
        new_score = change_data.get('new_score', 0)
        change_value = new_score - old_score
        
        return f"""
🔔 <b>Изменение ликвидности участка</b>

🔢 <b>Участок:</b> {cadastral_number}
📊 <b>Старый индекс:</b> {old_score:.2f}
📈 <b>Новый индекс:</b> {new_score:.2f}
📈 <b>Изменение:</b> {change_value:+.2f}

Ликвидность участка изменилась. Проверьте актуальную оценку.
        """.strip()
    
    else:
        return f"""
🔔 <b>Уведомление об участке</b>

🔢 <b>Участок:</b> {cadastral_number}
📝 <b>Тип изменения:</b> {change_type}
🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

Проверьте актуальную информацию в приложении.
        """.strip()


def format_error_message(error_message: str) -> str:
    """Форматирование сообщения об ошибке"""
    return f"""
❌ <b>Произошла ошибка</b>

{error_message}

Пожалуйста, попробуйте позже или обратитесь в поддержку.
    """.strip()


def format_help_message() -> str:
    """Форматирование справочного сообщения"""
    return """
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

<b>Поддержка:</b>
Если возникли вопросы, обратитесь: support@landliquidity.com
    """.strip()