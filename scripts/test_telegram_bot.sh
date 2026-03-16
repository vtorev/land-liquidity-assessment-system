#!/bin/bash

# Скрипт тестирования Telegram бота

set -e

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v pytest &> /dev/null; then
        log_info "Установка pytest..."
        pip install pytest pytest-asyncio
    fi
    
    log_success "Зависимости проверены"
}

# Запуск unit тестов
run_unit_tests() {
    log_info "Запуск unit тестов..."
    
    cd telegram_bot
    python -m pytest tests/ -v --cov=src --cov-report=html
    
    log_success "Unit тесты завершены"
}

# Тестирование API клиента
test_api_client() {
    log_info "Тестирование API клиента..."
    
    cd telegram_bot
    python -c "
import asyncio
from services.api_client import search_parcel, evaluate_liquidity

async def test_api():
    # Тест поиска участка
    result = await search_parcel('78:12:0000101:123')
    print(f'Поиск участка: {result}')
    
    # Тест оценки ликвидности
    evaluation_data = {
        'cadastral_number': '78:12:0000101:123',
        'area': 1000.0,
        'category': 'ИЖС'
    }
    result = await evaluate_liquidity(evaluation_data)
    print(f'Оценка ликвидности: {result}')

asyncio.run(test_api())
    "
    
    log_success "Тестирование API клиента завершено"
}

# Проверка валидаторов
test_validators() {
    log_info "Тестирование валидаторов..."
    
    cd telegram_bot
    python -c "
from utils.validators import validate_cadastral_number

# Тест валидации кадастровых номеров
test_cases = [
    ('78:12:0000101:123', True),
    ('77:01:0000101:001', True),
    ('78-12-0000101-123', False),
    ('invalid', False),
    ('', False)
]

for number, expected in test_cases:
    result = validate_cadastral_number(number)
    status = '✅' if result == expected else '❌'
    print(f'{status} {number}: {result} (ожидаемо: {expected})')
    "
    
    log_success "Тестирование валидаторов завершено"
}

# Проверка форматирования сообщений
test_formatters() {
    log_info "Тестирование форматирования сообщений..."
    
    cd telegram_bot