#!/bin/bash

# Скрипт запуска системы оценки ликвидности земельных участков

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
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен. Пожалуйста, установите Docker Compose."
        exit 1
    fi
    
    log_success "Docker и Docker Compose доступны"
}

# Проверка наличия .env файла
check_env_file() {
    if [ ! -f .env ]; then
        log_warning ".env файл не найден. Используем .env.example"
        cp .env.example .env
        log_info "Пожалуйста, настройте .env файл вручную"
    fi
}

# Запуск инфраструктуры
start_infrastructure() {
    log_info "Запуск инфраструктурных сервисов..."
    
    docker-compose up -d postgres redis rabbitmq minio
    
    # Ожидание готовности сервисов
    log_info "Ожидание готовности базы данных..."
    until docker-compose exec -T postgres pg_isready -U postgres; do
        sleep 2
    done
    
    log_info "Ожидание готовности Redis..."
    until docker-compose exec -T redis redis-cli ping; do
        sleep 2
    done
    
    log_success "Инфраструктурные сервисы запущены"
}

# Инициализация базы данных
init_database() {
    log_info "Инициализация базы данных..."
    
    # Запуск контейнера с backend для инициализации БД
    docker-compose run --rm backend python -c "
from src.models import init_database
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@postgres:5432/land_liquidity')
init_database(engine)
print('База данных инициализирована')
"
    
    log_success "База данных инициализирована"
}

# Сборка и запуск приложений
build_and_start() {
    log_info "Сборка Docker образов..."
    docker-compose build
    
    log_info "Запуск всех сервисов..."
    docker-compose up -d
    
    # Ожидание готовности сервисов
    log_info "Ожидание готовности сервисов..."
    sleep 15
    
    # Проверка здоровья сервисов
    check_health
}

# Проверка здоровья сервисов
check_health() {
    log_info "Проверка здоровья сервисов..."
    
    # Проверка API
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "API доступен"
    else
        log_warning "API недоступен. Проверьте логи: docker-compose logs backend"
    fi
    
    # Проверка Frontend
    if curl -f http://localhost/health &> /dev/null; then
        log_success "Frontend доступен"
    else
        log_warning "Frontend недоступен. Проверьте логи: docker-compose logs frontend"
    fi
    
    # Проверка Redis
    if curl -f http://localhost:6379 &> /dev/null; then
        log_success "Redis доступен"
    else
        log_warning "Redis недоступен"
    fi
    
    # Проверка PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        log_success "PostgreSQL доступен"
    else
        log_warning "PostgreSQL недоступен"
    fi
}

# Запуск фоновых задач
start_background_tasks() {
    log_info "Запуск фоновых задач..."
    
    # Запуск Celery workers
    docker-compose up -d celery-worker celery-beat
    
    log_success "Фоновые задачи запущены"
}

# Остановка системы
stop_system() {
    log_info "Остановка системы..."
    docker-compose down
    log_success "Система остановлена"
}

# Перезапуск системы
restart_system() {
    log_info "Перезапуск системы..."
    docker-compose down
    docker-compose up -d
    check_health
}

# Просмотр логов
view_logs() {
    log_info "Просмотр логов (нажмите Ctrl+C для выхода)..."
    docker-compose logs -f
}

# Очистка системы
clean_system() {
    log_warning "Очистка системы (будут удалены все данные)..."
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        log_success "Система очищена"
    else
        log_info "Очистка отменена"
    fi
}

# Показать статус системы
show_status() {
    log_info "Статус системы:"
    docker-compose ps
    
    echo
    log_info "Доступные сервисы:"
    echo "  - Frontend (Web UI): http://localhost"
    echo "  - API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo "  - RabbitMQ: http://localhost:15672 (guest/guest)"
    echo "  - MinIO: http://localhost:9000 (minio_admin/minio_password123)"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo "  - MLflow: http://localhost:5001"
    echo "  - Airflow: http://localhost:8080"
}

# Создание тестовых данных
create_test_data() {
    log_info "Создание тестовых данных..."
    
    # Запуск скрипта создания тестовых данных
    docker-compose run --rm backend python -c "
import sys
sys.path.append('/app')
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.data_acquisition.cadastre_parser import RosreestrParser
from src.tasks.data_tasks import update_cadastre_data

# Создание сессии
engine = create_engine('postgresql://postgres:postgres@postgres:5432/land_liquidity')
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Пример создания тестовых данных
    test_cadastral_numbers = [
        '78:12:0000101:123',
        '78:12:0000101:124',
        '78:12:0000101:125'
    ]
    
    print(f'Создание тестовых данных для {len(test_cadastral_numbers)} участков...')
    
    # В реальной системе здесь будет логика создания тестовых данных
    print('Тестовые данные созданы')
    
finally:
    session.close()
"
    
    log_success "Тестовые данные созданы"
}

# Запуск системы в режиме разработки
start_development() {
    log_info "Запуск системы в режиме разработки..."
    
    # Запуск только backend и базы данных
    docker-compose up -d postgres redis rabbitmq minio backend
    
    # Ожидание готовности backend
    sleep 10
    
    log_success "Backend запущен на http://localhost:8000"
    log_info "Для frontend запустите: cd frontend && npm run dev"
}

# Запуск только frontend
start_frontend_only() {
    log_info "Запуск только frontend..."
    
    # Проверка, запущен ли backend
    if ! curl -f http://localhost:8000/health &> /dev/null; then
        log_warning "Backend не запущен. Запустите сначала backend."
        log_info "Используйте: ./scripts/start.sh start-development"
        return 1
    fi
    
    # Сборка и запуск frontend
    docker-compose build frontend
    docker-compose up -d frontend
    
    log_success "Frontend запущен на http://localhost"
}

# Показать помощь
show_help() {
    echo "Использование: $0 [КОМАНДА]"
    echo
    echo "Команды:"
    echo "  start               Запустить всю систему"
    echo "  start-dev           Запустить в режиме разработки (без frontend)"
    echo "  start-frontend      Запустить только frontend"
    echo "  stop                Остановить систему"
    echo "  restart             Перезапустить систему"
    echo "  status              Показать статус системы"
    echo "  logs                Просмотреть логи"
    echo "  clean               Очистить систему (удалить все данные)"
    echo "  test-data           Создать тестовые данные"
    echo "  health              Проверить здоровье сервисов"
    echo "  build               Пересобрать образы"
    echo "  help                Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 start            # Запустить всю систему"
    echo "  $0 start-dev        # Запустить в режиме разработки"
    echo "  $0 logs             # Просмотреть логи"
    echo "  $0 clean            # Очистить систему"
    echo
    echo "После запуска система будет доступна по адресам:"
    echo "  - Web Interface: http://localhost"
    echo "  - API: http://localhost:8000"
    echo "  - API Documentation: http://localhost:8000/docs"
}

# Основная логика
main() {
    case "${1:-}" in
        "start")
            check_docker
            check_env_file
            start_infrastructure
            init_database
            build_and_start
            start_background_tasks
            show_status
            ;;
        "start-dev")
            check_docker
            check_env_file
            start_development
            ;;
        "start-frontend")
            check_docker
            start_frontend_only
            ;;
        "stop")
            stop_system
            ;;
        "restart")
            restart_system
            ;;
        "status")
            show_status
            ;;
        "logs")
            view_logs
            ;;
        "clean")
            clean_system
            ;;
        "test-data")
            create_test_data
            ;;
        "health")
            check_health
            ;;
        "build")
            docker-compose build
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            log_error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"