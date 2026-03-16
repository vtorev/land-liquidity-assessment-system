#!/bin/bash

# Скрипт запуска Telegram бота

set -e

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка переменных окружения
check_env() {
    log_info "Проверка переменных окружения..."
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        log_error "Не установлена переменная TELEGRAM_BOT_TOKEN"
        log_info "Установите: export TELEGRAM_BOT_TOKEN=your_bot_token"
        exit 1
    fi
    
    if [ -z "$POSTGRES_PASSWORD" ]; then
        log_error "Не установлена переменная POSTGRES_PASSWORD"
        log_info "Установите: export POSTGRES_PASSWORD=your_password"
        exit 1
    fi
    
    log_success "Переменные окружения проверены"
}

# Проверка доступности backend API
check_backend() {
    log_info "Проверка доступности backend API..."
    
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend API доступен"
    else
        log_error "Backend API недоступен. Запустите backend сначала."
        exit 1
    fi
}

# Сборка и запуск Telegram бота
start_bot() {
    log_info "Сборка и запуск Telegram бота..."
    
    cd telegram_bot
    
    # Сборка образа
    docker build -t land-liquidity-telegram-bot .
    
    # Запуск контейнера
    docker run -d \
        --name land-liquidity-telegram-bot \
        --env-file ../.env \
        -v $(pwd)/logs:/app/logs \
        --network likvid-network \
        land-liquidity-telegram-bot
    
    log_success "Telegram бот запущен"
}

# Проверка статуса бота
check_bot_status() {
    log_info "Проверка статуса Telegram бота..."
    
    if docker ps | grep -q land-liquidity-telegram-bot; then
        log_success "Telegram бот работает"
    else
        log_error "Telegram бот не запущен"
        docker logs land-liquidity-telegram-bot
        exit 1
    fi
}

# Основная логика
main() {
    log_info "Запуск Telegram бота для системы оценки ликвидности земельных участков"
    echo "========================================================================="
    
    check_env
    check_backend
    start_bot
    check_bot_status
    
    log_success "Telegram бот успешно запущен!"
    log_info "Бот доступен по ссылке: https://t.me/your_bot_name"
    log_info "Для остановки используйте: docker stop land-liquidity-telegram-bot"
}

# Запуск
main "$@"