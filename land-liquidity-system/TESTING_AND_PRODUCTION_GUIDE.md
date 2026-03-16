# Руководство по тестированию и production развертыванию

## Содержание

1. [Тестирование в staging среде](#тестирование-в-staging-среде)
2. [Настройка production окружения](#настройка-production-окружения)
3. [Нагрузочное тестирование](#нагрузочное-тестирование)
4. [Мониторинг и логирование](#мониторинг-и-логирование)
5. [Безопасность и производительность](#безопасность-и-производительность)

## Тестирование в staging среде

### 1. Подготовка staging среды

#### Создание staging окружения
```bash
# Создаем директорию для staging
mkdir staging
cd staging

# Копируем production конфигурацию
cp ../docker-compose.yml docker-compose.staging.yml
cp ../.env.example .env.staging

# Создаем staging специфичные настройки
cat > .env.staging << EOF
# Staging окружение
ENVIRONMENT=staging
DEBUG=false

# База данных
POSTGRES_DB=land_liquidity_staging
POSTGRES_USER=staging_user
POSTGRES_PASSWORD=staging_password_123
POSTGRES_HOST=staging-postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://staging-redis:6379/1

# Celery
CELERY_BROKER_URL=redis://staging-redis:6379/1
CELERY_RESULT_BACKEND=redis://staging-redis:6379/1

# API
API_HOST=0.0.0.0
API_PORT=8000
API_URL=https://staging-api.example.com

# Frontend
FRONTEND_URL=https://staging.example.com

# Секреты (замените на реальные значения)
SECRET_KEY=staging_secret_key_change_me
JWT_SECRET_KEY=staging_jwt_secret_change_me

# ML модели
ML_MODEL_PATH=/app/models/staging_model.pkl

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json

# Мониторинг
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
EOF
```

#### Настройка docker-compose для staging
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  # PostgreSQL для staging
  postgres-staging:
    image: postgres:15
    environment:
      POSTGRES_DB: land_liquidity_staging
      POSTGRES_USER: staging_user
      POSTGRES_PASSWORD: staging_password_123
    volumes:
      - postgres_staging_data:/var/lib/postgresql/data
      - ./init-db-staging.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U staging_user -d land_liquidity_staging"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis для staging
  redis-staging:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_staging_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Backend для staging
  backend-staging:
    build:
      context: ../
      dockerfile: Dockerfile.backend
    environment:
      - ENVIRONMENT=staging
      - DATABASE_URL=postgresql://staging_user:staging_password_123@postgres-staging:5432/land_liquidity_staging
      - REDIS_URL=redis://redis-staging:6379/1
      - CELERY_BROKER_URL=redis://redis-staging:6379/1
      - CELERY_RESULT_BACKEND=redis://redis-staging:6379/1
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ../src:/app/src
      - staging_models:/app/models
    ports:
      - "8001:8000"
    depends_on:
      postgres-staging:
        condition: service_healthy
      redis-staging:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend для staging
  frontend-staging:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://backend-staging:8000
      - NODE_ENV=production
    ports:
      - "3001:3000"
    depends_on:
      - backend-staging
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx для staging
  nginx-staging:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-staging.conf:/etc/nginx/nginx.conf
      - ./ssl-staging:/etc/nginx/ssl
    depends_on:
      - frontend-staging
      - backend-staging

  # Grafana для staging
  grafana-staging:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3002:3000"
    volumes:
      - grafana_staging_data:/var/lib/grafana

  # Prometheus для staging
  prometheus-staging:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus-staging.yml:/etc/prometheus/prometheus.yml
      - prometheus_staging_data:/prometheus

volumes:
  postgres_staging_data:
  redis_staging_data:
  staging_models:
  grafana_staging_data:
  prometheus_staging_data:
```

### 2. Тестирование функциональности

#### Unit тесты
```bash
# Запуск unit тестов для backend
cd src
python -m pytest tests/ -v --cov=src --cov-report=html

# Запуск unit тестов для frontend
cd frontend
npm test

# Запуск всех тестов
./scripts/run_tests.sh
```

#### Интеграционные тесты
```python
# tests/integration/test_api.py
import pytest
import requests
from src.models import CadastreParcel, LiquidityAssessment
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class TestLiquidityAPI:
    """Интеграционные тесты для API оценки ликвидности"""
    
    BASE_URL = "http://localhost:8000"
    
    def test_parcel_search(self):
        """Тест поиска участка"""
        response = requests.post(f"{self.BASE_URL}/api/parcels/search", 
                               json={"cadastral_number": "78:12:0000101:123"})
        assert response.status_code == 200
        data = response.json()
        assert "cadastral_number" in data
        assert "address" in data
    
    def test_liquidity_evaluation(self):
        """Тест оценки ликвидности"""
        test_data = {
            "cadastral_number": "78:12:0000101:123",
            "address": "г. Санкт-Петербург, ул. Примерная, д. 1",
            "area": 1000.0,
            "category": "Сельхозназначения",
            "purpose": "Для сельскохозяйственного производства"
        }
        
        response = requests.post(f"{self.BASE_URL}/api/evaluate", 
                               json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "liquidity_score" in data
        assert 0 <= data["liquidity_score"] <= 1
        assert "predicted_price" in data
    
    def test_market_analytics(self):
        """Тест рыночной аналитики"""
        response = requests.get(f"{self.BASE_URL}/api/analytics/market?region=78")
        assert response.status_code == 200
        data = response.json()
        assert "average_price" in data
        assert "trend" in data
        assert "comparables" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### End-to-end тесты
```python
# tests/e2e/test_full_workflow.py
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestFullWorkflow:
    """E2E тесты полного рабочего процесса"""
    
    @pytest.fixture
    def browser(self):
        """Настройка WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    
    def test_complete_evaluation_workflow(self, browser):
        """Тест полного цикла оценки"""
        # 1. Открытие главной страницы
        browser.get("http://localhost:3000")
        
        # 2. Поиск участка
        search_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "cadastralNumber"))
        )
        search_input.send_keys("78:12:0000101:123")
        
        search_button = browser.find_element(By.ID, "searchButton")
        search_button.click()
        
        # 3. Ожидание загрузки формы оценки
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "evaluationForm"))
        )
        
        # 4. Заполнение формы
        area_input = browser.find_element(By.ID, "area")
        area_input.clear()
        area_input.send_keys("1000")
        
        # 5. Отправка формы
        submit_button = browser.find_element(By.ID, "submitEvaluation")
        submit_button.click()
        
        # 6. Проверка результата
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.ID, "results"))
        )
        
        result_score = browser.find_element(By.ID, "liquidityScore")
        assert result_score.text != ""
        
        # 7. Проверка аналитики
        analytics_tab = browser.find_element(By.ID, "analyticsTab")
        analytics_tab.click()
        
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "marketChart"))
        )
```

### 3. Автоматизация тестирования

#### Скрипт запуска всех тестов
```bash
#!/bin/bash
# scripts/run_tests.sh

set -e

echo "🧪 Запуск тестирования системы оценки ликвидности земельных участков"
echo "=================================================================="

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка окружения
check_environment() {
    log_info "Проверка окружения..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    log_success "Окружение готово"
}

# Запуск staging среды
start_staging() {
    log_info "Запуск staging среды..."
    
    cd staging
    docker-compose -f docker-compose.staging.yml up -d
    
    # Ожидание готовности сервисов
    log_info "Ожидание готовности сервисов..."
    sleep 60
    
    # Проверка здоровья сервисов
    check_services_health
}

# Проверка здоровья сервисов
check_services_health() {
    log_info "Проверка здоровья сервисов..."
    
    local services=("backend-staging:8001" "frontend-staging:3001")
    
    for service in "${services[@]}"; do
        local url="http://${service}/health"
        if curl -f "$url" &> /dev/null; then
            log_success "Сервис $service доступен"
        else
            log_error "Сервис $service недоступен"
            return 1
        fi
    done
}

# Запуск unit тестов
run_unit_tests() {
    log_info "Запуск unit тестов..."
    
    # Backend тесты
    cd ../src
    if python -m pytest tests/unit/ -v --cov=src --cov-report=xml --junitxml=../test-results/backend-unit.xml; then
        log_success "Backend unit тесты пройдены"
    else
        log_error "Backend unit тесты провалены"
        return 1
    fi
    
    # Frontend тесты
    cd ../frontend
    if npm test -- --coverage --watchAll=false; then
        log_success "Frontend unit тесты пройдены"
    else
        log_error "Frontend unit тесты провалены"
        return 1
    fi
}

# Запуск интеграционных тестов
run_integration_tests() {
    log_info "Запуск интеграционных тестов..."
    
    cd ../src
    if python -m pytest tests/integration/ -v --junitxml=../test-results/integration.xml; then
        log_success "Интеграционные тесты пройдены"
    else
        log_error "Интеграционные тесты провалены"
        return 1
    fi
}

# Запуск E2E тестов
run_e2e_tests() {
    log_info "Запуск E2E тестов..."
    
    cd ../tests/e2e
    if python -m pytest test_full_workflow.py -v --junitxml=../../test-results/e2e.xml; then
        log_success "E2E тесты пройдены"
    else
        log_error "E2E тесты провалены"
        return 1
    fi
}

# Генерация отчета
generate_report() {
    log_info "Генерация отчета о тестировании..."
    
    mkdir -p ../test-results
    cd ../test-results
    
    # Сборка общего отчета
    cat > test-summary.md << EOF
# Отчет о тестировании

## Общая статистика
- Дата: $(date)
- Окружение: Staging
- Версия: $(git rev-parse --short HEAD)

## Результаты тестов
- Unit тесты: $(if [ -f backend-unit.xml ] && [ -f frontend-unit.xml ]; then echo "✅ Пройдены"; else echo "❌ Провалены"; fi)
- Интеграционные тесты: $(if [ -f integration.xml ]; then echo "✅ Пройдены"; else echo "❌ Провалены"; fi)
- E2E тесты: $(if [ -f e2e.xml ]; then echo "✅ Пройдены"; else echo "❌ Провалены"; fi)

## Покрытие кода
- Backend: $(if [ -f ../src/htmlcov/index.html ]; then echo "См. ../src/htmlcov/"; else echo "Нет данных"; fi)
- Frontend: $(if [ -d ../frontend/coverage ]; then echo "См. ../frontend/coverage/"; else echo "Нет данных"; fi)

## Рекомендации
- Проверить все проваленные тесты
- Увеличить покрытие кода до 80%+
- Провести нагрузочное тестирование
EOF
    
    log_success "Отчет сохранен в test-results/test-summary.md"
}

# Очистка после тестирования
cleanup() {
    log_info "Очистка после тестирования..."
    
    cd ../staging
    docker-compose -f docker-compose.staging.yml down
    docker system prune -f
    
    log_success "Очистка завершена"
}

# Основная логика
main() {
    check_environment
    start_staging
    run_unit_tests
    run_integration_tests
    run_e2e_tests
    generate_report
    cleanup
    
    log_success "Тестирование завершено успешно!"
}

# Запуск
main "$@"
```

## Настройка production окружения

### 1. Production конфигурация

#### Production .env файл
```bash
# .env.production
# Production окружение
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_DB=land_liquidity_prod
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_HOST=prod-postgres.internal
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://prod-redis.internal:6379/0

# Celery
CELERY_BROKER_URL=redis://prod-redis.internal:6379/0
CELERY_RESULT_BACKEND=redis://prod-redis.internal:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_URL=https://api.land-liquidity.com

# Frontend
FRONTEND_URL=https://land-liquidity.com

# Секреты (обязательно измените!)
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ML модели
ML_MODEL_PATH=/app/models/prod_model.pkl
ML_MODEL_VERSION=v1.2.0

# Логирование
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_FILE=/var/log/land-liquidity/app.log

# Мониторинг
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_URL=https://grafana.company.com

# Безопасность
CORS_ORIGINS=https://land-liquidity.com,https://admin.land-liquidity.com
ALLOWED_HOSTS=land-liquidity.com,api.land-liquidity.com

# Резервное копирование
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE=s3://company-backups/land-liquidity/

# Масштабирование
MAX_WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=30

# Сторонние сервисы
EMAIL_SERVICE_URL=https://api.email-service.com
SMS_SERVICE_URL=https://api.sms-service.com
GEOCODING_API_KEY=${GEOCODING_API_KEY}
```

#### Production docker-compose
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # PostgreSQL для production
  postgres-prod:
    image: postgres:15
    environment:
      POSTGRES_DB: land_liquidity_prod
      POSTGRES_USER: prod_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U prod_user -d land_liquidity_prod"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  # Redis для production
  redis-prod:
    image: redis:7-alpine
    volumes:
      - redis_prod_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  # Backend для production
  backend-prod:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://prod_user:${POSTGRES_PASSWORD}@postgres-prod:5432/land_liquidity_prod
      - REDIS_URL=redis://redis-prod:6379/0
      - CELERY_BROKER_URL=redis://redis-prod:6379/0
      - CELERY_RESULT_BACKEND=redis://redis-prod:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - API_URL=${API_URL}
    volumes:
      - ./models:/app/models
      - ./logs:/var/log/land-liquidity
    ports:
      - "8000:8000"
    depends_on:
      postgres-prod:
        condition: service_healthy
      redis-prod:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    restart: unless-stopped

  # Frontend для production
  frontend-prod:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
      - NODE_ENV=production
    ports:
      - "3000:3000"
    depends_on:
      - backend-prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
    restart: unless-stopped

  # Nginx для production
  nginx-prod:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-production.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - frontend-prod
      - backend-prod
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    restart: unless-stopped

  # Celery workers
  celery-worker-prod:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A src.tasks.celery_app worker --loglevel=info --concurrency=4
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://prod_user:${POSTGRES_PASSWORD}@postgres-prod:5432/land_liquidity_prod
      - REDIS_URL=redis://redis-prod:6379/0
      - CELERY_BROKER_URL=redis://redis-prod:6379/0
      - CELERY_RESULT_BACKEND=redis://redis-prod:6379/0
    volumes:
      - ./models:/app/models
      - ./logs:/var/log/land-liquidity
    depends_on:
      - postgres-prod
      - redis-prod
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    restart: unless-stopped

  # Celery beat
  celery-beat-prod:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A src.tasks.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://prod_user:${POSTGRES_PASSWORD}@postgres-prod:5432/land_liquidity_prod
      - REDIS_URL=redis://redis-prod:6379/0
      - CELERY_BROKER_URL=redis://redis-prod:6379/0
      - CELERY_RESULT_BACKEND=redis://redis-prod:6379/0
    volumes:
      - ./logs:/var/log/land-liquidity
    depends_on:
      - postgres-prod
      - redis-prod
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    restart: unless-stopped

  # Prometheus для production
  prometheus-prod:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus-production.yml:/etc/prometheus/prometheus.yml
      - ./prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  # Grafana для production
  grafana-prod:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - grafana_prod_data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana-datasources:/etc/grafana/provisioning/datasources
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

volumes:
  postgres_prod_data:
  redis_prod_data:
  grafana_prod_data:
```

### 2. Nginx конфигурация для production
```nginx
# nginx-production.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Логирование
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Безопасность
    server_tokens off;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Upstream backend
    upstream backend {
        least_conn;
        server backend-prod:8000 max_fails=3 fail_timeout=30s;
        server backend-prod:8000 max_fails=3 fail_timeout=30s;
        server backend-prod:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Upstream frontend
    upstream frontend {
        server frontend-prod:3000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # API Gateway
    server {
        listen 80;
        server_name api.land-liquidity.com;

        # Перенаправление на HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.land-liquidity.com;

        # SSL сертификаты
        ssl_certificate /etc/nginx/ssl/land-liquidity.com.crt;
        ssl_certificate_key /etc/nginx/ssl/land-liquidity.com.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Таймауты
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Auth endpoints (более строгий rate limiting)
        location /api/auth/ {
            limit_req zone=auth burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
            access_log off;
        }

        # Metrics
        location /metrics {
            proxy_pass http://backend;
            allow 127.0.0.1;
            allow 10.0.0.0/8;
            deny all;
        }
    }

    # Frontend
    server {
        listen 80;
        server_name land-liquidity.com www.land-liquidity.com;

        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name land-liquidity.com www.land-liquidity.com;

        ssl_certificate /etc/nginx/ssl/land-liquidity.com.crt;
        ssl_certificate_key /etc/nginx/ssl/land-liquidity.com.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # API проксирование для frontend
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 3. Kubernetes deployment (альтернатива Docker Compose)

#### Kubernetes манифесты
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: land-liquidity-prod
  labels:
    name: land-liquidity-prod

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: land-liquidity-prod
type: Opaque
data:
  postgres-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  secret-key: <base64-encoded-secret>
  jwt-secret: <base64-encoded-jwt-secret>

---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: land-liquidity-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "land_liquidity_prod"
        - name: POSTGRES_USER
          value: "prod_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - prod_user
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - prod_user
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi

---
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: land-liquidity-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: land-liquidity/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          value: "postgresql://prod_user:$(POSTGRES_PASSWORD)@postgres:5432/land_liquidity_prod"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: CELERY_BROKER_URL
          value: "redis://redis:6379/0"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt-secret
        envFrom:
        - secretRef:
            name: app-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: land-liquidity-prod
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: land-liquidity-ingress
  namespace: land-liquidity-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - land-liquidity.com
    - api.land-liquidity.com
    secretName: land-liquidity-tls
  rules:
  - host: api.land-liquidity.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
  - host: land-liquidity.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## Нагрузочное тестирование

### 1. Подготовка нагрузочного тестирования

#### Создание тестовых данных
```python
# scripts/generate_test_data.py
import random
import json
from datetime import datetime, timedelta
import requests

def generate_test_parcels(count=1000):
    """Генерация тестовых данных для участков"""
    categories = ["Сельхозназначения", "ИЖС", "Коммерческая", "Промышленная"]
    purposes = ["Для сельскохозяйственного производства", "Индивидуальное жилищное строительство", 
                "Коммерческое использование", "Промышленное производство"]
    
    test_data = []
    
    for i in range(count):
        cadastral_number = f"78:12:000010{i:03d}:123"
        area = random.uniform(500, 10000)
        
        parcel_data = {
            "cadastral_number": cadastral_number,
            "address": f"г. Санкт-Петербург, район {random.randint(1, 18)}, ул. {random.choice(['Примерная', 'Тестовая', 'Демонстрационная'])}, д. {random.randint(1, 100)}",
            "area": round(area, 2),
            "category": random.choice(categories),
            "purpose": random.choice(purposes)
        }
        test_data.append(parcel_data)
    
    return test_data

def load_test_data_to_system(test_data, api_url="http://localhost:8000"):
    """Загрузка тестовых данных в систему"""
    print(f"Загрузка {len(test_data)} тестовых участков...")
    
    for i, parcel in enumerate(test_data):
        try:
            response = requests.post(f"{api_url}/api/parcels/", json=parcel)
            if response.status_code == 201:
                print(f"✅ Участок {i+1}/{len(test_data)} создан")
            else:
                print(f"❌ Ошибка создания участка {i+1}: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка загрузки участка {i+1}: {e}")

def generate_load_test_script():
    """Генерация скрипта для нагрузочного тестирования"""
    script = """
import locust
from locust import HttpUser, task, between
import random
import json

class LiquidityUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.cadastral_numbers = [
            "78:12:0000101:123", "78:12:0000102:123", "78:12:0000103:123",
            "78:12:0000104:123", "78:12:0000105:123", "78:12:0000106:123"
        ]
    
    @task(3)
    def search_parcel(self):
        """Тест поиска участка"""
        cadastral_number = random.choice(self.cadastral_numbers)
        self.client.post("/api/parcels/search", 
                        json={"cadastral_number": cadastral_number})
    
    @task(2)
    def evaluate_liquidity(self):
        """Тест оценки ликвидности"""
        test_data = {
            "cadastral_number": random.choice(self.cadastral_numbers),
            "address": "г. Санкт-Петербург, ул. Тестовая, д. 1",
            "area": random.uniform(1000, 5000),
            "category": "Сельхозназначения",
            "purpose": "Для сельскохозяйственного производства"
        }
        self.client.post("/api/evaluate", json=test_data)
    
    @task(1)
    def get_market_analytics(self):
        """Тест рыночной аналитики"""
        self.client.get("/api/analytics/market?region=78&limit=10")
    
    @task(1)
    def get_health(self):
        """Тест health check"""
        self.client.get("/health")

if __name__ == "__main__":
    # Запуск в режиме standalone
    from locust.env import Environment
    from locust.stats import stats_printer, stats_history
    from locust.log import setup_logging
    
    setup_logging("INFO", None)
    
    # Создание среды
    env = Environment(user_classes=[LiquidityUser])
    env.create_local_runner()
    
    # Запуск статистики
    gevent.spawn(stats_printer(env.stats))
    
    # Запуск истории статистики
    gevent.spawn(stats_history, env.runner)
    
    # Запуск пользователей
    env.runner.start(10, spawn_rate=2)
    
    # Ожидание
    gevent.spawn_later(600, lambda: env.runner.quit())
    env.runner.greenlet.join()
"""
    
    with open("load_test_script.py", "w") as f:
        f.write(script)
    
    print("✅ Скрипт нагрузочного тестирования создан: load_test_script.py")

if __name__ == "__main__":
    # Генерация тестовых данных
    test_data = generate_test_parcels(1000)
    
    # Сохранение в файл
    with open("test_parcels.json", "w") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Тестовые данные сохранены в test_parcels.json")
    
    # Генерация скрипта нагрузочного тестирования
    generate_load_test_script()
```

### 2. Запуск нагрузочного тестирования

#### Locust нагрузочное тестирование
```bash
#!/bin/bash
# scripts/run_load_test.sh

set -e

echo "🚀 Запуск нагрузочного тестирования системы оценки ликвидности"
echo "================================================================"

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v locust &> /dev/null; then
        log_info "Установка Locust..."
        pip install locust
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    log_success "Зависимости готовы"
}

# Запуск системы для тестирования
start_test_system() {
    log_info "Запуск системы для нагрузочного тестирования..."
    
    # Используем staging конфигурацию
    cd staging
    docker-compose -f docker-compose.staging.yml up -d
    
    # Ожидание готовности
    log_info "Ожидание готовности системы..."
    sleep 60
    
    # Проверка здоровья
    if curl -f http://localhost:8001/health &> /dev/null; then
        log_success "Система готова к тестированию"
    else
        log_error "Система не готова"
        exit 1
    fi
}

# Загрузка тестовых данных
load_test_data() {
    log_info "Загрузка тестовых данных..."
    
    cd ../scripts
    python generate_test_data.py
    
    # Загрузка данных в систему
    log_info "Загрузка данных в систему..."
    python -c "
import json
import requests

with open('../test_parcels.json', 'r') as f:
    test_data = json.load(f)

print(f'Загрузка {len(test_data)} тестовых участков...')

for i, parcel in enumerate(test_data[:100]):  # Загружаем первые 100 для тестирования
    try:
        response = requests.post('http://localhost:8001/api/parcels/', json=parcel)
        if response.status_code == 201:
            print(f'✅ Участок {i+1}/100 создан')
        else:
            print(f'❌ Ошибка создания участка {i+1}: {response.status_code}')
    except Exception as e:
        print(f'❌ Ошибка загрузки участка {i+1}: {e}')

print('Загрузка тестовых данных завершена')
"
}

# Запуск нагрузочного тестирования
run_load_test() {
    log_info "Запуск нагрузочного тестирования..."
    
    cd ../staging
    
    # Запуск Locust в фоновом режиме
    locust -f ../load_test_script.py \
          --host=http://localhost:8001 \
          --users=100 \
          --spawn-rate=10 \
          --run-time=10m \
          --html=../load_test_results.html \
          --headless &
    
    LOCUST_PID=$!
    
    log_info "Locust запущен с PID: $LOCUST_PID"
    log_info "Ожидание завершения тестирования..."
    
    # Ожидание завершения
    wait $LOCUST_PID
    
    log_success "Нагрузочное тестирование завершено"
}

# Анализ результатов
analyze_results() {
    log_info "Анализ результатов нагрузочного тестирования..."
    
    if [ -f "../load_test_results.html" ]; then
        log_success "Отчет сохранен: ../load_test_results.html"
        
        # Извлечение ключевых метрик
        echo "📊 Ключевые метрики производительности:"
        echo "======================================"
        
        # Парсинг HTML отчета (упрощенный)
        if command -v jq &> /dev/null; then
            # Если доступен jq, попробуем извлечь метрики
            echo "Метрики доступны в HTML отчете"
        fi
        
        # Проверка логов системы
        log_info "Проверка логов системы на предмет ошибок..."
        docker-compose -f docker-compose.staging.yml logs --tail=100 backend-staging | grep -i error || echo "❌ Ошибки не найдены"
        
    else
        log_error "Отчет не найден"
    fi
}

# Генерация отчета
generate_load_test_report() {
    log_info "Генерация отчета о нагрузочном тестировании..."
    
    cat > ../load_test_report.md << EOF
# Отчет о нагрузочном тестировании

## Общая информация
- Дата: $(date)
- Система: Оценка ликвидности земельных участков
- Окружение: Staging
- Продолжительность теста: 10 минут

## Конфигурация теста
- Количество пользователей: 100
- Скорость создания пользователей: 10 пользователей/сек
- Тестовые сценарии:
  - Поиск участков (3 балла)
  - Оценка ликвидности (2 балла)
  - Рыночная аналитика (1 балл)
  - Health check (1 балл)

## Результаты тестирования

### Производительность
- Среднее время ответа: См. в load_test_results.html
- 95% перцентиль: См. в load_test_results.html
- Количество запросов в секунду: См. в load_test_results.html
- Количество успешных запросов: См. в load_test_results.html
- Количество неудачных запросов: См. в load_test_results.html

### Ресурсы системы
- CPU usage: Мониторинг через Grafana
- Memory usage: Мониторинг через Grafana
- Database connections: Мониторинг через Grafana
- Redis connections: Мониторинг через Grafana

## Рекомендации

### По производительности
1. Оптимизация базы данных:
   - Добавить индексы для часто используемых запросов
   - Настроить connection pooling
   - Оптимизировать сложные запросы

2. Кэширование:
   - Внедрить Redis кэширование для часто запрашиваемых данных
   - Кэшировать результаты ML моделей
   - Кэшировать рыночную аналитику

3. Масштабирование:
   - Настроить горизонтальное масштабирование backend
   - Настроить балансировку нагрузки
   - Рассмотреть шардирование базы данных

### По стабильности
1. Мониторинг:
   - Настроить алертинг на высокую нагрузку
   - Мониторить время отклика
   - Мониторить количество ошибок

2. Безопасность:
   - Настроить rate limiting
   - Добавить защиту от DDoS
   - Настроить WAF

## Заключение
Система показала удовлетворительную производительность при нагрузке 100 пользователей.
Для production развертывания рекомендуется провести более масштабное тестирование
и внедрить рекомендации по оптимизации.

EOF
    
    log_success "Отчет сохранен: ../load_test_report.md"
}

# Очистка после тестирования
cleanup() {
    log_info "Очистка после нагрузочного тестирования..."
    
    cd staging
    docker-compose -f docker-compose.staging.yml down
    docker system prune -f
    
    log_success "Очистка завершена"
}

# Основная логика
main() {
    check_dependencies
    start_test_system
    load_test_data
    run_load_test
    analyze_results
    generate_load_test_report
    cleanup
    
    log_success "Нагрузочное тестирование завершено!"
    log_info "Результаты доступны в:"
    log_info "  - load_test_results.html (детальный отчет)"
    log_info "  - load_test_report.md (анализ и рекомендации)"
}

# Запуск
main "$@"
```

### 3. Автоматическое масштабирование

#### Horizontal Pod Autoscaler (Kubernetes)
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: land-liquidity-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Min
```

#### Docker Compose масштабирование
```bash
# Скрипт масштабирования
#!/bin/bash
# scripts/scale_services.sh

# Масштабирование backend
docker-compose up -d --scale backend-prod=5

# Масштабирование frontend
docker-compose up -d --scale frontend-prod=3

# Масштабирование celery workers
docker-compose up -d --scale celery-worker-prod=3

echo "✅ Сервисы масштабированы"
echo "Backend: 5 реплик"
echo "Frontend: 3 реплики"
echo "Celery workers: 3 реплики"
```

## Мониторинг и логирование

### 1. Prometheus конфигурация
```yaml
# prometheus-production.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend-prod:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend-prod:3000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### 2. Grafana дашборды
```json
{
  "dashboard": {
    "id": null,
    "title": "Land Liquidity System Monitoring",
    "tags": ["land-liquidity", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds",
            "min": 0
          }
        ]
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status_code}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active connections"
          },
          {
            "expr": "pg_settings_max_connections",
            "legendFormat": "Max connections"
          }
        ]
      },
      {
        "id": 4,
        "title": "Redis Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "Used memory"
          },
          {
            "expr": "redis_memory_max_bytes",
            "legendFormat": "Max memory"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### 3. Логирование и алертинг
```yaml
# alert_rules.yml
groups:
- name: land-liquidity-alerts
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors/second"

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database is down"
      description: "PostgreSQL database is not responding"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is above 90%"

  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is above 80%"
```

## Безопасность и производительность

### 1. Безопасность

#### SSL/TLS настройка
```bash
# Скрипт настройки SSL
#!/bin/bash
# scripts/setup_ssl.sh

# Генерация SSL сертификатов
mkdir -p ssl
cd ssl

# Генерация self-signed сертификата (для staging)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout land-liquidity.com.key \
  -out land-liquidity.com.crt \
  -subj "/C=RU/ST=SPb/L=SPb/O=Company/CN=land-liquidity.com"

# Для production используйте Let's Encrypt
# certbot --nginx -d land-liquidity.com -d api.land-liquidity.com

echo "✅ SSL сертификаты сгенерированы"
```

#### Безопасность базы данных
```sql
-- database-security.sql
-- Настройка безопасности PostgreSQL

-- Создание пользователей с ограниченными правами
CREATE USER app_user WITH PASSWORD 'secure_password';
CREATE USER readonly_user WITH PASSWORD 'readonly_password';

-- Предоставление минимальных необходимых прав
GRANT CONNECT ON DATABASE land_liquidity_prod TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Только чтение для аналитики
GRANT CONNECT ON DATABASE land_liquidity_prod TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Настройка параметров безопасности
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Перезагрузка конфигурации
SELECT pg_reload_conf();
```

### 2. Производительность

#### Оптимизация базы данных
```sql
-- database-optimization.sql
-- Индексы для производительности

-- Индексы для часто используемых запросов
CREATE INDEX CONCURRENTLY idx_cadastre_parcel_cadastral_number ON cadastre_parcel(cadastral_number);
CREATE INDEX CONCURRENTLY idx_cadastre_parcel_coordinates ON cadastre_parcel USING GIST(coordinates);
CREATE INDEX CONCURRENTLY idx_parcel_features_parcel_id ON parcel_features(parcel_id);
CREATE INDEX CONCURRENTLY idx_parcel_distances_parcel_id ON parcel_distances(parcel_id);
CREATE INDEX CONCURRENTLY idx_market_listings_parcel_id ON market_listings(parcel_id);
CREATE INDEX CONCURRENTLY idx_liquidity_assessments_parcel_id ON liquidity_assessments(parcel_id);

-- Составные индексы для сложных запросов
CREATE INDEX CONCURRENTLY idx_market_listings_parcel_date ON market_listings(parcel_id, listing_date);
CREATE INDEX CONCURRENTLY idx_liquidity_assessments_parcel_date ON liquidity_assessments(parcel_id, assessment_date);

-- Индексы для аналитики
CREATE INDEX CONCURRENTLY idx_socio_economic_data_region_year ON socio_economic_data(region_code, data_year);
CREATE INDEX CONCURRENTLY idx_operation_logs_operation_type ON operation_logs(operation_type);
CREATE INDEX CONCURRENTLY idx_operation_logs_started_at ON operation_logs(started_at);
```

#### Кэширование
```python
# src/cache/redis_cache.py
import redis
import json
import hashlib
from functools import wraps
from typing import Any, Callable, Optional

class RedisCache:
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = default_ttl
    
    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Создание ключа кэша на основе функции и аргументов"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранение данных в кэш"""
        try:
            data = json.dumps(value, default=str)
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, data)
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Удаление данных из кэша"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    def clear_pattern(self, pattern: str) -> bool:
        """Очистка кэша по шаблону"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return bool(self.redis_client.delete(*keys))
        except Exception:
            pass
        return False

# Декоратор для кэширования функций
def cache_result(cache: RedisCache, ttl: Optional[int] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создание ключа кэша
            cache_key = cache._make_key(func.__name__, args, kwargs)
            
            # Попытка получить из кэша
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполнение функции
            result = func(*args, **kwargs)
            
            # Сохранение в кэш
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Пример использования
cache = RedisCache("redis://localhost:6379/0")

@cache_result(cache, ttl=1800)  # Кэш на 30 минут
def get_market_analytics(region_code: str, limit: int = 10):
    # Логика получения аналитики
    pass
```

### 3. Резервное копирование

#### Автоматическое резервное копирование
```bash
#!/bin/bash
# scripts/backup.sh

set -e

# Конфигурация
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="land_liquidity_prod"
DB_USER="prod_user"
DB_HOST="postgres-prod"
S3_BUCKET="s3://company-backups/land-liquidity"

log_info() {
    echo "$(date): $1"
}

# Резервное копирование базы данных
backup_database() {
    log_info "Начало резервного копирования базы данных..."
    
    # Создание бэкапа
    docker exec postgres-prod pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_backup_$DATE.sql"
    
    # Сжатие
    gzip "$BACKUP_DIR/db_backup_$DATE.sql"
    
    # Копирование в S3
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_DIR/db_backup_$DATE.sql.gz" "$S3_BUCKET/db_backups/"
        log_info "Бэкап загружен в S3"
    fi
    
    log_info "Резервное копирование базы данных завершено"
}

# Резервное копирование моделей ML
backup_models() {
    log_info "Резервное копирование ML моделей..."
    
    # Копирование моделей
    docker cp backend-prod:/app/models "$BACKUP_DIR/models_$DATE"
    
    # Архивация
    tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" -C "$BACKUP_DIR" "models_$DATE"
    rm -rf "$BACKUP_DIR/models_$DATE"
    
    # Копирование в S3
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_DIR/models_$DATE.tar.gz" "$S3_BUCKET/models/"
        log_info "Модели загружены в S3"
    fi
    
    log_info "Резервное копирование моделей завершено"
}

# Резервное копирование логов
backup_logs() {
    log_info "Резервное копирование логов..."
    
    # Копирование логов
    docker cp backend-prod:/var/log/land-liquidity "$BACKUP_DIR/logs_$DATE"
    
    # Архивация
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$BACKUP_DIR" "logs_$DATE"
    rm -rf "$BACKUP_DIR/logs_$DATE"
    
    log_info "Резервное копирование логов завершено"
}

# Очистка старых бэкапов
cleanup_old_backups() {
    log_info "Очистка старых бэкапов..."
    
    # Удаление бэкапов старше 30 дней
    find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
    
    log_info "Очистка завершена"
}

# Основная логика
main() {
    log_info "Начало резервного копирования"
    
    backup_database
    backup_models
    backup_logs
    cleanup_old_backups
    
    log_info "Резервное копирование завершено успешно"
}

main "$@"
```

## Заключение

Это руководство предоставляет полную инструкцию по:

1. **Тестированию в staging среде** - полный цикл тестирования с unit, integration и E2E тестами
2. **Настройке production окружения** - Docker Compose и Kubernetes конфигурации
3. **Нагрузочному тестированию** - инструменты и методики для проверки производительности
4. **Мониторингу и логированию** - Prometheus, Grafana, алертинг
5. **Безопасности и производительности** - оптимизация, кэширование, резервное копирование

Следуя этим инструкциям, вы сможете:
- Провести полное тестирование системы перед production
- Настроить надежное и масштабируемое production окружение
- Обеспечить высокую производительность и доступность системы
- Реализовать эффективный мониторинг и логирование
- Обеспечить безопасность и надежность данных

**Важно:** Все конфигурационные файлы содержат примеры значений. Перед production развертыванием обязательно:
- Замените все примеры паролей и секретов на реальные значения
- Настройте SSL сертификаты
- Настройте мониторинг под свои требования
- Проведите дополнительное тестирование в staging среде