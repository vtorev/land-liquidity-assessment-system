#!/bin/bash

# Быстрый запуск системы оценки ликвидности земельных участков

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Пожалуйста, установите Docker."
        echo "Инструкции: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен. Пожалуйста, установите Docker Compose."
        echo "Инструкции: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_success "Docker и Docker Compose доступны"
}

# Проверка наличия .env файла
check_env_file() {
    if [ ! -f .env ]; then
        log_warning ".env файл не найден. Используем .env.example"
        cp .env.example .env
        log_info "Пожалуйста, настройте .env файл вручную при необходимости"
    fi
}

# Быстрый запуск системы
quick_start() {
    log_info "🚀 Запуск системы оценки ликвидности земельных участков..."
    
    # Проверка предварительных условий
    check_docker
    check_env_file
    
    # Сборка и запуск системы
    log_info "📦 Сборка Docker образов..."
    docker-compose build --no-cache
    
    log_info "🚀 Запуск всех сервисов..."
    docker-compose up -d
    
    # Ожидание готовности сервисов
    log_info "⏳ Ожидание готовности сервисов..."
    sleep 30
    
    # Проверка здоровья сервисов
    check_services_health
    
    # Отображение информации о запуске
    show_startup_info
}

# Проверка здоровья сервисов
check_services_health() {
    log_info "🔍 Проверка здоровья сервисов..."
    
    local services_ok=0
    local total_services=6
    
    # Проверка API
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "✅ API сервис доступен"
        ((services_ok++))
    else
        log_error "❌ API сервис недоступен"
    fi
    
    # Проверка Frontend
    if curl -f http://localhost/health &> /dev/null; then
        log_success "✅ Frontend доступен"
        ((services_ok++))
    else
        log_error "❌ Frontend недоступен"
    fi
    
    # Проверка PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        log_success "✅ PostgreSQL доступен"
        ((services_ok++))
    else
        log_error "❌ PostgreSQL недоступен"
    fi
    
    # Проверка Redis
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        log_success "✅ Redis доступен"
        ((services_ok++))
    else
        log_error "❌ Redis недоступен"
    fi
    
    # Проверка RabbitMQ
    if curl -f http://localhost:15672 &> /dev/null; then
        log_success "✅ RabbitMQ доступен"
        ((services_ok++))
    else
        log_error "❌ RabbitMQ недоступен"
    fi
    
    # Проверка MinIO
    if curl -f http://localhost:9000/minio/health/live &> /dev/null; then
        log_success "✅ MinIO доступен"
        ((services_ok++))
    else
        log_error "❌ MinIO недоступен"
    fi
    
    log_info "📊 Результаты проверки: $services_ok/$total_services сервисов доступны"
    
    if [ $services_ok -eq $total_services ]; then
        log_success "🎉 Все сервисы успешно запущены!"
    else
        log_warning "⚠️  Некоторые сервисы могут быть еще в процессе запуска"
        log_info "   Проверьте логи: ./scripts/start.sh logs"
    fi
}

# Отображение информации о запуске
show_startup_info() {
    echo
    echo "=================================================================="
    log_success "🎉 Система успешно запущена!"
    echo "=================================================================="
    echo
    log_info "🌐 Веб-интерфейс: http://localhost"
    log_info "🔌 API: http://localhost:8000"
    log_info "📚 API Documentation: http://localhost:8000/docs"
    echo
    log_info "📊 Мониторинг и администрирование:"
    log_info "   - Grafana: http://localhost:3000 (admin/admin)"
    log_info "   - RabbitMQ: http://localhost:15672 (guest/guest)"
    log_info "   - MinIO: http://localhost:9000 (minio_admin/minio_password123)"
    log_info "   - PostgreSQL: localhost:5432"
    log_info "   - Redis: localhost:6379"
    log_info "   - MLflow: http://localhost:5001"
    log_info "   - Airflow: http://localhost:8080"
    echo
    log_info "🛠️  Управление системой:"
    log_info "   - Просмотр логов: ./scripts/start.sh logs"
    log_info "   - Проверка статуса: ./scripts/start.sh status"
    log_info "   - Остановка системы: ./scripts/start.sh stop"
    echo
    log_info "📚 Документация:"
    log_info "   - Основная документация: README.md"
    log_info "   - Руководство по развертыванию: DEPLOYMENT.md"
    log_info "   - Frontend документация: WEB_APP_README.md"
    echo
    log_info "💡 Советы:"
    log_info "   - Для разработки используйте: ./scripts/start.sh start-dev"
    log_info "   - Для frontend разработки: cd frontend && npm run dev"
    log_info "   - Для создания тестовых данных: ./scripts/start.sh test-data"
    echo "=================================================================="
}

# Показать помощь
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo
    echo "Быстрый запуск системы оценки ликвидности земельных участков"
    echo
    echo "ОПЦИИ:"
    echo "  -h, --help     Показать эту справку"
    echo "  --clean        Очистить систему перед запуском"
    echo "  --dev          Запустить в режиме разработки"
    echo
    echo "ПРИМЕРЫ:"
    echo "  $0             Запустить систему"
    echo "  $0 --clean     Очистить и запустить систему"
    echo "  $0 --dev       Запустить в режиме разработки"
    echo
    echo "После запуска система будет доступна по адресу: http://localhost"
}

# Очистка системы
clean_system() {
    log_warning "🧹 Очистка системы..."
    read -p "Вы уверены, что хотите очистить систему? Это удалит все данные (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        log_success "✅ Система очищена"
    else
        log_info "❌ Очистка отменена"
        exit 1
    fi
}

# Режим разработки
dev_mode() {
    log_info "🔧 Запуск в режиме разработки..."
    
    # Проверка предварительных условий
    check_docker
    check_env_file
    
    # Запуск только backend и базы данных
    docker-compose up -d postgres redis rabbitmq minio backend
    
    # Ожидание готовности backend
    sleep 15
    
    log_success "✅ Backend запущен на http://localhost:8000"
    log_info "💡 Для frontend запустите: cd frontend && npm run dev"
    log_info "💡 Frontend будет доступен на http://localhost:3000"
}

# Основная логика
main() {
    case "${1:-}" in
        "--help"|"-h")
            show_help
            ;;
        "--clean")
            clean_system
            quick_start
            ;;
        "--dev")
            dev_mode
            ;;
        "")
            quick_start
            ;;
        *)
            log_error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
}

# Проверка, что скрипт запущен из правильной директории
if [ ! -f "docker-compose.yml" ]; then
    log_error "Скрипт должен быть запущен из корневой директории проекта"
    log_info "Пожалуйста, перейдите в директорию с проектом и запустите скрипт снова"
    exit 1
fi

# Запуск основной функции
main "$@"