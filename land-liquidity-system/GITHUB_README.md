# Система оценки ликвидности земельных участков 🏛️

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-20+-blue.svg)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Современная система для оценки ликвидности земельных участков с использованием машинного обучения, анализа рыночных данных и Telegram бота.

## ✨ Особенности

- 🤖 **ML-модели**: CatBoost и Random Forest для точной оценки ликвидности
- 📊 **Рыночный анализ**: Интеграция с Avito, Циан и другими платформами
- 📱 **Telegram бот**: Удобный доступ через популярный мессенджер
- 🗺️ **Геоанализ**: OpenStreetMap, спутниковые снимки, инфраструктура
- 🐳 **Docker**: Полностью контейнеризированная система
- 🔧 **Celery**: Асинхронные задачи и фоновая обработка
- 📈 **Визуализация**: Интерактивный веб-интерфейс с графиками и картами
- 🚀 **CI/CD**: Автоматическая сборка и деплой

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  ML Models      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│  (CatBoost)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Telegram Bot   │    │   Celery        │    │   PostgreSQL    │
│   (Python)      │    │   (Tasks)       │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Market APIs   │    │   Redis         │    │   Nginx         │
│   (Avito, Циан) │    │   (Cache)       │    │   (Proxy)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1. Клонирование репозитория

```bash
git clone https://github.com/ваш-username/land-liquidity-assessment-system.git
cd land-liquidity-assessment-system
```

### 2. Настройка окружения

```bash
# Копирование .env.example
cp .env.example .env

# Редактирование конфигурации
nano .env  # или используйте ваш любимый редактор
```

### 3. Запуск системы

```bash
# Запуск всей системы
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 4. Доступ к сервисам

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Admin панель**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs

## 📖 Документация

- [Разработка](DEVELOPMENT_PLAN.md) - План разработки и архитектура
- [Развертывание](DEPLOYMENT.md) - Production deployment
- [Тестирование](TESTING_AND_PRODUCTION_GUIDE.md) - Тестирование и production
- [Beget хостинг](BEGET_DEPLOYMENT_GUIDE.md) - Деплой на Beget
- [Telegram бот](TELEGRAM_BOT_INTEGRATION.md) - Интеграция Telegram бота

## 🛠️ Структура проекта

```
├── src/                          # Backend (Python)
│   ├── api/                      # FastAPI endpoints
│   ├── data_acquisition/         # Парсеры данных
│   ├── feature_engineering/      # Расчет признаков
│   ├── ml/                       # ML модели
│   ├── models.py                 # SQLAlchemy models
│   └── tasks/                    # Celery задачи
├── frontend/                     # Frontend (React)
│   ├── src/
│   │   ├── components/           # React компоненты
│   │   ├── pages/               # Страницы
│   │   └── styles/              # Стили
│   └── Dockerfile
├── telegram_bot/                 # Telegram бот
├── config/                       # Конфигурация
├── scripts/                      # Скрипты развертывания
├── .github/workflows/            # CI/CD workflows
└── docker-compose.yml           # Docker orchestration
```

## 🔧 Конфигурация

### Основные переменные окружения

```bash
# База данных
POSTGRES_DB=land_liquidity
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Backend
SECRET_KEY=your_secret_key
DEBUG=False

# ML модели
MODEL_PATH=/app/models/
MODEL_VERSION=1.0

# Telegram бот
TELEGRAM_BOT_TOKEN=your_bot_token

# Market APIs
AVITO_API_KEY=your_api_key
CIAN_API_KEY=your_api_key
```

## 🤖 ML Модели

### Доступные модели

1. **CatBoost Regressor** - Регрессия для оценки цены
2. **CatBoost Classifier** - Классификация ликвидности
3. **Random Forest** - Альтернативная модель

### Признаки для оценки

- Географическое положение
- Инфраструктура (школы, больницы, транспорт)
- Рыночные данные
- Площадь и категория участка
- Спутниковые снимки
- Экономические показатели региона

## 📊 API Endpoints

### Основные endpoints

```bash
# Поиск участка
GET /api/parcels/search?cadastral_number=78:12:0000101:123

# Оценка ликвидности
POST /api/evaluate
{
  "cadastral_number": "78:12:0000101:123",
  "area": 1000,
  "category": "ИЖС"
}

# Рыночная аналитика
GET /api/analytics/market?region=Москва&limit=10

# История оценок
GET /api/assessments/user/{user_id}
```

## 🐳 Docker

### Сборка образов

```bash
# Сборка всех сервисов
docker-compose build

# Сборка конкретного сервиса
docker-compose build backend
docker-compose build frontend
```

### Запуск в production

```bash
# Production запуск
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Мониторинг
docker-compose logs -f
docker-compose ps
```

## 🧪 Тестирование

### Backend тесты

```bash
# Запуск тестов
docker-compose exec backend python -m pytest

# Покрытие кода
docker-compose exec backend python -m pytest --cov=src --cov-report=html
```

### Frontend тесты

```bash
# Запуск тестов
docker-compose exec frontend npm test

# Покрытие кода
docker-compose exec frontend npm run test:coverage
```

## 🚀 Production деплой

### 1. Подготовка сервера

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка SSL

```bash
# Генерация SSL сертификатов (Let's Encrypt)
docker run --rm -it \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly \
  --standalone -d your-domain.com
```

### 3. Запуск production

```bash
# Копирование production конфигурации
cp docker-compose.prod.yml docker-compose.yml

# Запуск
docker-compose up -d
```

## 🤖 Telegram Бот

### Возможности бота

- Поиск участков по кадастровому номеру
- Оценка ликвидности участков
- Рыночная аналитика
- Уведомления об изменениях
- Интерактивное меню

### Запуск бота

```bash
# Запуск Telegram бота
docker-compose -f docker-compose.telegram.yml up -d

# Проверка логов
docker-compose -f docker-compose.telegram.yml logs -f telegram-bot
```

## 📈 Мониторинг

### Prometheus + Grafana

```bash
# Запуск мониторинга
docker-compose -f docker-compose.monitoring.yml up -d

# Доступ
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9090
```

## 🤝 Участие в разработке

### 1. Форк и клонирование

```bash
git clone https://github.com/ваш-username/land-liquidity-assessment-system.git
cd land-liquidity-assessment-system
```

### 2. Создание ветки

```bash
git checkout -b feature/your-feature-name
```

### 3. Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск локально
docker-compose up
```

### 4. Тестирование

```bash
# Запуск тестов
make test

# Проверка кода
make lint
```

### 5. Pull Request

1. Запушьте изменения: `git push origin feature/your-feature-name`
2. Создайте Pull Request на GitHub
3. Дождитесь CI/CD проверки
4. Получите ревью и мерж

## 📄 Лицензия

Этот проект лицензирован по лицензии MIT - смотрите файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- [CatBoost](https://catboost.ai/) - За мощные ML модели
- [FastAPI](https://fastapi.tiangolo.com/) - За быстрый и удобный API
- [React](https://reactjs.org/) - За гибкий frontend
- [Docker](https://docker.com/) - За контейнеризацию
- [PostgreSQL](https://postgresql.org/) - За надежную базу данных

## 📞 Контакты

- **Разработчик**: [Ваше Имя]
- **Email**: your.email@example.com
- **Telegram**: @your_username

---

⭐ Если проект вам понравился, поставьте звезду на GitHub!