# Инструкция по загрузке системы на GitHub

## 🎯 Целевой репозиторий
**URL:** https://github.com/vtorev/land-liquidity-assessment-system.git

## 🚀 Быстрая загрузка

### 1. Запуск автоматического скрипта

```bash
# Перейдите в директорию проекта
cd d:/vibe-coding/likvid

# Запустите скрипт загрузки
python scripts/upload_to_github.py https://github.com/vtorev/land-liquidity-assessment-system.git
```

### 2. Что делает скрипт

Скрипт автоматически выполнит все необходимые шаги:

1. **Проверка Git** - Убедится, что Git установлен и настроен
2. **Инициализация репозитория** - Создаст локальный Git репозиторий
3. **Добавление файлов** - Добавит все файлы в индекс Git
4. **Создание коммита** - Создаст первый коммит с подробным описанием
5. **Добавление удаленного репозитория** - Подключит ваш GitHub репозиторий
6. **Загрузка на GitHub** - Запушит код на GitHub

### 3. Ручная загрузка (если скрипт не работает)

Если по каким-то причинам скрипт не работает, выполните команды вручную:

```bash
# Инициализация Git
git init

# Добавление файлов
git add .

# Проверка статуса
git status

# Создание коммита
git commit -m "Initial commit: Land liquidity assessment system with ML models and Telegram bot

Features:
- Backend API (Python/FastAPI) with ML models (CatBoost, Random Forest)
- Frontend application (React) with interactive maps and visualization
- Telegram bot for convenient access
- Docker containerization for all services
- Celery for asynchronous tasks
- PostgreSQL database
- Redis for caching
- CI/CD with GitHub Actions
- Complete documentation and deployment guides"

# Добавление удаленного репозитория
git remote add origin https://github.com/vtorev/land-liquidity-assessment-system.git

# Загрузка на GitHub
git branch -M main
git push -u origin main
```

## 🔐 Аутентификация на GitHub

### Вариант 1: GitHub CLI (рекомендуется)

1. **Установите GitHub CLI:**
   ```bash
   # Windows
   winget install GitHub.cli
   
   # macOS
   brew install gh
   
   # Linux
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   ```

2. **Аутентифицируйтесь:**
   ```bash
   gh auth login
   # Следуйте инструкциям
   ```

3. **Запустите загрузку:**
   ```bash
   python scripts/upload_to_github.py https://github.com/vtorev/land-liquidity-assessment-system.git
   ```

### Вариант 2: Personal Access Token

1. **Создайте токен на GitHub:**
   - Перейдите в Settings → Developer settings → Personal access tokens
   - Нажмите "Generate new token (classic)"
   - Заполните:
     - Note: `Git operations`
     - Expiration: установите срок действия
     - Scopes: выберите `repo`
   - Скопируйте токен

2. **Используйте токен при push:**
   ```bash
   git push https://USERNAME:TOKEN@github.com/USERNAME/REPO.git
   ```

## 📋 Проверка загрузки

После успешной загрузки:

1. **Перейдите на GitHub:**
   - Откройте https://github.com/vtorev/land-liquidity-assessment-system
   - Проверьте, что все файлы загружены

2. **Проверьте ветки:**
   - Должна быть ветка `main`
   - Коммит должен быть с описанием "Initial commit"

3. **Проверьте файлы:**
   - `README.md` - Основная документация
   - `docker-compose.yml` - Docker конфигурация
   - `src/` - Backend код
   - `frontend/` - Frontend код
   - `telegram_bot/` - Telegram бот
   - `.github/workflows/` - CI/CD workflows

## 🚀 Настройка CI/CD

### 1. Добавление секретов

1. Перейдите в репозиторий на GitHub
2. Нажмите Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"
4. Добавьте следующие секреты:

| Имя | Значение | Описание |
|-----|----------|----------|
| `DOCKER_USERNAME` | Ваш username Docker Hub | Для сборки Docker образов |
| `DOCKER_PASSWORD` | Ваш пароль Docker Hub | Для сборки Docker образов |
| `POSTGRES_PASSWORD` | Пароль для PostgreSQL | Для базы данных |
| `SECRET_KEY` | Секретный ключ | Для backend безопасности |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | Для Telegram интеграции |
| `AVITO_API_KEY` | API ключ Avito | Для парсинга данных |
| `CIAN_API_KEY` | API ключ Циан | Для парсинга данных |

### 2. Запуск CI/CD

1. **Создайте новый коммит:**
   ```bash
   git add .
   git commit -m "Setup CI/CD secrets"
   git push origin main
   ```

2. **Проверьте Actions:**
   - Перейдите в репозитории на вкладку "Actions"
   - Должен запуститься workflow
   - Проверьте статус выполнения

### 3. Настройка production деплоя

1. **Создайте production ветку:**
   ```bash
   git checkout -b production
   git push origin production
   ```

2. **Настройте environment:**
   - Перейдите в Settings → Environments
   - Создайте environment "production"
   - Настройте protection rules

## 🎉 Готово!

Теперь ваша система загружена на GitHub и готова к совместной разработке!

### 📞 Что дальше:

1. **Пригласите команду:**
   - Settings → Collaborators
   - Добавьте участников

2. **Настройте проект:**
   - Issues → Labels - создайте метки
   - Projects - настройте доску задач

3. **Начните разработку:**
   - Создавайте feature ветки
   - Делайте pull requests
   - Используйте CI/CD для автоматизации

## 🛠️ Устранение проблем

### Проблема: Git не установлен
**Решение:** Установите Git с [официального сайта](https://git-scm.com/)

### Проблема: Ошибка аутентификации
**Решение:** Используйте GitHub CLI или создайте Personal Access Token

### Проблема: Ошибка push
**Решение:** Проверьте URL репозитория и права доступа

### Проблема: CI/CD не запускается
**Решение:** Проверьте наличие файлов в `.github/workflows/` и настройку секретов

## 📄 Полезные ссылки

- [GitHub Documentation](https://docs.github.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Docker on GitHub](https://docs.docker.com/ci-cd/github-actions/)
- [Git Tutorial](https://git-scm.com/docs/gittutorial)

---

✅ **Система успешно загружена на GitHub!**
🌐 **Репозиторий:** https://github.com/vtorev/land-liquidity-assessment-system