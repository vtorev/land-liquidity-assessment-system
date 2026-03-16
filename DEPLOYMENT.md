# Руководство по развертыванию системы оценки ликвидности земельных участков

## Быстрый старт

### Требования

- Docker и Docker Compose
- Git
- 8GB RAM (рекомендуется 16GB)
- 20GB свободного места на диске

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd land-liquidity-assessment
```

### 2. Настройка окружения

```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование конфигурации (опционально)
nano .env
```

### 3. Запуск системы

```bash
# Запуск всей системы
./scripts/start.sh start

# Проверка статуса
./scripts/start.sh status

# Просмотр логов
./scripts/start.sh logs
```

### 4. Проверка работоспособности

Откройте в браузере:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)

## Архитектура системы

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   Auth Service  │
│   (React/TS)    │◄──►│   (FastAPI)      │◄──►│   (JWT/OAuth)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Evaluation    │    │   Data Service   │    │   ML Service    │
│   Service       │◄──►│   (ETL/Parser)   │◄──►│   (CatBoost)    │
│   (FastAPI)     │    │   (Celery)       │    │   (SHAP)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cache         │    │   PostgreSQL     │    │   MongoDB       │
│   (Redis)       │    │   + PostGIS      │    │   (Raw Data)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐
│   Scheduler     │    │   External APIs  │
│   (Airflow)     │    │   (OSM, Yandex)  │
└─────────────────┘    └──────────────────┘
```

## Сервисы

### Backend Services

- **Backend API** (порт 8000): Основной API сервис
- **PostgreSQL** (порт 5432): Основная база данных с PostGIS
- **Redis** (порт 6379): Кэширование и очереди
- **RabbitMQ** (порт 5672/15672): Асинхронные задачи
- **MinIO** (порт 9000): Хранение файлов (аналог S3)

### ML и аналитика

- **MLflow** (порт 5001): Управление ML экспериментами
- **OSRM** (порт 5000): Маршрутизация
- **Celery Workers**: Фоновые задачи обработки данных

### Мониторинг

- **Prometheus** (порт 9090): Сбор метрик
- **Grafana** (порт 3000): Визуализация метрик
- **Airflow** (порт 8080): Оркестрация ETL процессов

## Команды управления

### Основные команды

```bash
# Запуск системы
./scripts/start.sh start

# Остановка системы
./scripts/start.sh stop

# Перезапуск системы
./scripts/start.sh restart

# Проверка статуса
./scripts/start.sh status

# Просмотр логов
./scripts/start.sh logs

# Проверка здоровья
./scripts/start.sh health
```

### Дополнительные команды

```bash
# Создание тестовых данных
./scripts/start.sh test-data

# Пересборка образов
./scripts/start.sh build

# Очистка системы (удаление всех данных)
./scripts/start.sh clean

# Помощь
./scripts/start.sh help
```

## API Endpoints

### Основные endpoints

- `GET /health` - Проверка работоспособности
- `POST /parcels/search` - Поиск участка
- `POST /evaluate` - Оценка ликвидности
- `GET /assessments/{id}` - Получение результата оценки
- `GET /market/comparables` - Сопоставимые продажи
- `GET /analytics/market-trends` - Рыночные тренды

### Пример использования API

```bash
# Поиск участка по кадастровому номеру
curl -X POST "http://localhost:8000/parcels/search" \
  -H "Content-Type: application/json" \
  -d '{"cadastral_number": "78:12:0000101:123"}'

# Оценка ликвидности
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"cadastral_number": "78:12:0000101:123"}'
```

## Разработка

### Локальная разработка

1. **Запуск только инфраструктуры:**
   ```bash
   docker-compose up -d postgres redis rabbitmq minio
   ```

2. **Запуск backend в режиме разработки:**
   ```bash
   cd src
   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Запуск frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Тестирование

```bash
# Запуск unit тестов
pytest tests/

# Запуск тестов с coverage
pytest tests/ --cov=src --cov-report=html

# Запуск линтеров
flake8 src/
black --check src/
isort --check-only src/
```

### CI/CD

Система включает GitHub Actions workflow для:
- Автоматического тестирования
- Сборки Docker образов
- Развертывания в staging и production

## Мониторинг

### Grafana Dashboards

После запуска системы доступны предустановленные дашборды:
- **System Overview**: Общее состояние системы
- **API Metrics**: Метрики API (RPS, latency, errors)
- **Database Performance**: Производительность базы данных
- **ML Model Performance**: Производительность ML моделей

### Prometheus Metrics

Основные метрики:
- `api_requests_total` - Количество запросов к API
- `api_request_duration_seconds` - Время выполнения запросов
- `model_predictions_total` - Количество предсказаний моделей
- `celery_tasks_total` - Количество выполненных задач

## Безопасность

### Аутентификация
- JWT токены для API
- Ограничение частоты запросов
- Валидация всех входных данных

### Сетевая безопасность
- Все сервисы изолированы в Docker сети
- Доступ к базе данных только изнутри сети
- HTTPS для production окружения

### Данные
- Шифрование чувствительных данных
- Регулярные бэкапы
- Ограничение доступа к данным

## Производительность

### Оптимизация

1. **База данных:**
   - Индексы для геометрических данных
   - Оптимизация запросов
   - Read replicas для масштабирования

2. **Кэширование:**
   - Redis для кэширования результатов
   - Кэширование геометрических расчетов
   - Кэширование внешних API вызовов

3. **Асинхронная обработка:**
   - Celery для фоновых задач
   - Очереди для обработки данных
   - Параллельная обработка

### Масштабирование

1. **Горизонтальное масштабирование:**
   ```bash
   # Масштабирование backend
   docker-compose up -d --scale backend=3
   
   # Масштабирование workers
   docker-compose up -d --scale celery-worker=5
   ```

2. **Kubernetes:**
   - Helm charts для production
   - Автоматическое масштабирование
   - Load balancing

## Troubleshooting

### Частые проблемы

1. **Сервисы не запускаются:**
   ```bash
   # Проверка логов
   docker-compose logs [service-name]
   
   # Пересборка образов
   docker-compose build --no-cache
   ```

2. **База данных не доступна:**
   ```bash
   # Проверка подключения
   docker-compose exec postgres pg_isready -U postgres
   
   # Пересоздание базы данных
   docker-compose down -v
   docker-compose up -d postgres
   ```

3. **API не отвечает:**
   ```bash
   # Проверка здоровья
   curl http://localhost:8000/health
   
   # Проверка логов backend
   docker-compose logs backend
   ```

### Логи

```bash
# Просмотр всех логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs backend
docker-compose logs celery-worker

# Сохранение логов
docker-compose logs > logs.txt
```

## Production Deployment

### Подготовка

1. **Настройка .env для production:**
   ```bash
   # Отключить debug режим
   DEBUG=false
   
   # Настроить production базу данных
   DATABASE_URL=postgresql://user:pass@prod-db:5432/land_liquidity
   
   # Настроить production Redis
   REDIS_URL=redis://prod-redis:6379/0
   ```

2. **SSL/TLS:**
   - Настроить Nginx с SSL сертификатами
   - Использовать Let's Encrypt для бесплатных сертификатов

3. **Бэкапы:**
   ```bash
   # Регулярный бэкап базы данных
   docker-compose exec postgres pg_dump -U postgres land_liquidity > backup.sql
   
   # Бэкап файлов
   tar -czf files_backup.tar.gz /path/to/files
   ```

### Kubernetes Deployment

Система готова для развертывания в Kubernetes:
- Helm charts в `k8s/`
- ConfigMaps и Secrets
- Deployment и Service манифесты
- Ingress для внешнего доступа

## Поддержка

### Контакты
- Email: support@landliquidity.com
- Telegram: @land_liquidity_support

### Документация
- [API Documentation](http://localhost:8000/docs)
- [Development Guide](DEVELOPMENT_PLAN.md)
- [Architecture](README.md)

### Issue Tracking
- GitHub Issues для багов и фич
- Документация в Wiki
- Примеры использования в Examples/

## Лицензия

Этот проект лицензирован в соответствии с MIT License - подробности см. в файле LICENSE.