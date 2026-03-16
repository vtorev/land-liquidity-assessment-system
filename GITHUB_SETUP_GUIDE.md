# Инструкция по созданию GitHub репозитория для системы оценки ликвидности земельных участков

## Содержание

1. [Создание репозитория на GitHub](#создание-репозитория-на-github)
2. [Инициализация Git локально](#инициализация-git-локально)
3. [Первый коммит](#первый-коммит)
4. [Настройка удаленного репозитория](#настройка-удаленного-репозитория)
5. [Загрузка кода на GitHub](#загрузка-кода-на-github)
6. [Настройка CI/CD](#настройка-cicd)
7. [Дополнительные настройки](#дополнительные-настройки)

## Создание репозитория на GitHub

### 1. Регистрация на GitHub (если еще не зарегистрированы)

1. Перейдите на [github.com](https://github.com)
2. Нажмите "Sign up" (Зарегистрироваться)
3. Заполните форму регистрации:
   - Имя пользователя
   - Email
   - Пароль
4. Подтвердите регистрацию по email

### 2. Создание нового репозитория

1. Войдите в свой аккаунт GitHub
2. Нажмите на значок "+" в правом верхнем углу
3. Выберите "New repository" (Новый репозиторий)
4. Заполните поля:
   - **Repository name**: `land-liquidity-assessment-system`
   - **Description**: `Система оценки ликвидности земельных участков с ML-моделями и Telegram ботом`
   - **Visibility**: Public (если хотите, чтобы репозиторий был публичным)
5. Поставьте галочку "Add a README file"
6. Выберите "Add .gitignore" → Python
7. Выберите "Choose a license" → MIT License
8. Нажмите "Create repository"

## Инициализация Git локально

### 1. Проверка установки Git

```bash
git --version
```

Если Git не установлен, скачайте и установите с [официального сайта](https://git-scm.com/)

### 2. Настройка Git (если еще не настроили)

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "ваш@email.com"
```

### 3. Инициализация репозитория в проекте

```bash
cd d:/vibe-coding/likvid
git init
```

## Первый коммит

### 1. Добавление файлов в индекс

```bash
git add .
```

### 2. Проверка статуса

```bash
git status
```

### 3. Создание первого коммита

```bash
git commit -m "Initial commit: Land liquidity assessment system with ML models and Telegram bot"
```

## Настройка удаленного репозитория

### 1. Получение URL репозитория

На странице вашего репозитория на GitHub:
1. Нажмите зеленую кнопку "Code"
2. Скопируйте URL (выберите HTTPS или SSH)

Пример URL: `https://github.com/ваш-username/land-liquidity-assessment-system.git`

### 2. Добавление удаленного репозитория

```bash
git remote add origin https://github.com/ваш-username/land-liquidity-assessment-system.git
```

### 3. Проверка удаленного репозитория

```bash
git remote -v
```

## Загрузка кода на GitHub

### 1. Первый push

```bash
git branch -M main
git push -u origin main
```

### 2. Аутентификация

При первом push вас попросят ввести:
- Имя пользователя GitHub
- Пароль (или токен доступа)

**Важно**: GitHub больше не поддерживает аутентификацию по паролю для Git операций. Вам нужно создать Personal Access Token:

1. Перейдите в Settings → Developer settings → Personal access tokens
2. Нажмите "Generate new token"
3. Выберите "Generate new token (classic)"
4. Заполните:
   - Note: `Git operations`
   - Expiration: установите срок действия
   - Scopes: выберите `repo`
5. Нажмите "Generate token"
6. Скопируйте токен (он покажется только один раз!)

### 3. Использование токена

При запросе пароля введите ваш Personal Access Token.

## Настройка CI/CD

### 1. GitHub Actions уже настроены

В вашем проекте уже есть готовые workflow файлы:
- `.github/workflows/ci.yml` - для CI/CD
- `.github/workflows/deploy.yml` - для деплоя

### 2. Настройка секретов (Secrets)

Для работы CI/CD нужно добавить секреты в репозиторий:

1. Перейдите в Settings → Secrets and variables → Actions
2. Нажмите "New repository secret"
3. Добавьте следующие секреты:

| Имя | Значение |
|-----|----------|
| `DOCKER_USERNAME` | Ваш username Docker Hub |
| `DOCKER_PASSWORD` | Ваш пароль Docker Hub |
| `POSTGRES_PASSWORD` | Пароль для PostgreSQL |
| `SECRET_KEY` | Секретный ключ для Django/Flask |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота |
| `API_KEY` | API ключи для внешних сервисов |

## Дополнительные настройки

### 1. Защита ветки main

1. Перейдите в Settings → Branches
2. Нажмите "Add rule"
3. Настройте правила:
   - Require a pull request before merging
   - Require approvals: 1
   - Dismiss stale PR approvals when new commits are pushed
   - Require status checks to pass before merging

### 2. Уведомления

1. Перейдите в Settings → Notifications
2. Настройте уведомления о:
   - Новых issues
   - Pull requests
   - Упоминаниях

### 3. Issues и Project Management

1. Перейдите в Issues → Labels
2. Создайте метки:
   - `bug` - Красный
   - `enhancement` - Синий
   - `feature` - Зеленый
   - `help wanted` - Желтый
   - `documentation` - Фиолетовый

### 4. Wiki и Documentation

1. Перейдите в Settings
2. Включите Wiki
3. Добавьте документацию:
   - Установка
   - Разработка
   - Деплой
   - API документация

## Проверка загрузки

### 1. Проверка файлов

После загрузки проверьте, что все файлы появились в репозитории:
- `README.md`
- `docker-compose.yml`
- `src/` - backend код
- `frontend/` - frontend код
- `telegram_bot/` - Telegram бот
- `.github/workflows/` - CI/CD workflows

### 2. Проверка CI/CD

1. Создайте новый коммит
2. Перейдите в Actions
3. Проверьте, что workflow запустился и прошел успешно

## Команды для повседневной работы

### 1. Работа с репозиторием

```bash
# Проверка статуса
git status

# Добавление изменений
git add .

# Создание коммита
git commit -m "Описание изменений"

# Загрузка на GitHub
git push origin main

# Получение обновлений
git pull origin main
```

### 2. Работа с ветками

```bash
# Создание новой ветки
git checkout -b feature-name

# Переключение между ветками
git checkout main
git checkout feature-name

# Объединение веток
git checkout main
git merge feature-name

# Удаление ветки
git branch -d feature-name
```

### 3. Работа с Pull Requests

1. Создайте ветку: `git checkout -b feature-name`
2. Внесите изменения и закоммитьте
3. Запушьте ветку: `git push origin feature-name`
4. На GitHub создайте Pull Request
5. Дождитесь ревью и мержа

## Устранение проблем

### 1. Ошибка аутентификации

Если возникает ошибка аутентификации:
```bash
git config --global credential.helper store
```

### 2. Конфликты при merge

```bash
# Просмотр конфликтов
git status

# Ручное разрешение конфликтов в файлах

# После разрешения
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### 3. Большой размер репозитория

Если репозиторий слишком большой:
```bash
# Проверка размера
git count-objects -vH

# Очистка кэша
git gc --aggressive --prune=now
```

## Готово!

Теперь ваш проект загружен на GitHub и готов к совместной разработке. 

**Следующие шаги:**
1. Пригласите команду в репозиторий
2. Настройте CI/CD окружение
3. Начните разработку по Agile methodology
4. Документируйте процесс разработки

## Полезные ссылки

- [GitHub Documentation](https://docs.github.com/)
- [Git Tutorial](https://git-scm.com/docs/gittutorial)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Docker on GitHub](https://docs.docker.com/ci-cd/github-actions/)