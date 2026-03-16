"""Клавиатуры главного меню"""

from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Получение клавиатуры главного меню"""
    keyboard = [
        [
            KeyboardButton("🔍 Поиск участка"),
            KeyboardButton("📊 Оценить ликвидность")
        ],
        [
            KeyboardButton("📈 Рыночная аналитика"),
            KeyboardButton("⚙️ Настройки")
        ],
        [
            KeyboardButton("❓ Помощь")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )


def get_search_results_keyboard(cadastral_number: str) -> ReplyKeyboardMarkup:
    """Получение клавиатуры результатов поиска"""
    keyboard = [
        [
            KeyboardButton("💰 Оценить ликвидность"),
            KeyboardButton("📈 Показать аналитику")
        ],
        [
            KeyboardButton("📋 Дополнительная информация"),
            KeyboardButton("🔔 Подписаться на уведомления")
        ],
        [
            KeyboardButton("⬅️ Назад в меню")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_evaluation_keyboard() -> ReplyKeyboardMarkup:
    """Получение клавиатуры для оценки"""
    keyboard = [
        [
            KeyboardButton("🏠 ИЖС"),
            KeyboardButton("🏢 Коммерческая")
        ],
        [
            KeyboardButton("🌾 Сельхозназначения"),
            KeyboardButton("🏭 Промышленная")
        ],
        [
            KeyboardButton("⬅️ Назад")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_analytics_keyboard() -> ReplyKeyboardMarkup:
    """Получение клавиатуры для аналитики"""
    keyboard = [
        [
            KeyboardButton("регионы"),
            KeyboardButton("📊 По районам")
        ],
        [
            KeyboardButton("📈 Тренды цен"),
            KeyboardButton("📊 Сравнительный анализ")
        ],
        [
            KeyboardButton("⬅️ Назад")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_settings_keyboard() -> ReplyKeyboardMarkup:
    """Получение клавиатуры настроек"""
    keyboard = [
        [
            KeyboardButton("🔔 Уведомления"),
            KeyboardButton("📊 Частота аналитики")
        ],
        [
            KeyboardButton("👤 Мои подписки"),
            KeyboardButton("🗑️ Очистить данные")
        ],
        [
            KeyboardButton("⬅️ Назад")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    """Получение клавиатуры Да/Нет"""
    keyboard = [
        [
            KeyboardButton("Да"),
            KeyboardButton("Нет")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Получение клавиатуры "Назад"""
    keyboard = [
        [
            KeyboardButton("⬅️ Назад")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )