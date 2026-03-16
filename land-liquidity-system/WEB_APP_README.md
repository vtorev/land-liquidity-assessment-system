# Веб-приложение для оценки ликвидности земельных участков

## Обзор

Веб-приложение представляет собой современный frontend интерфейс для системы оценки ликвидности земельных участков. Приложение построено на React с использованием TypeScript, Next.js и Tailwind CSS.

## Особенности

### 🎯 Основные функции
- **Поиск участков** по кадастровому номеру
- **Оценка ликвидности** с использованием AI-моделей
- **Визуализация результатов** с подробной аналитикой
- **Рыночная аналитика** в реальном времени
- **История оценок** и сравнение результатов

### 🎨 Дизайн и UX
- **Современный интерфейс** с адаптивной версткой
- **Пошаговый процесс** оценки для удобства пользователей
- **Интуитивная навигация** и прогресс-бар
- **Анимации и эффекты** для улучшения пользовательского опыта
- **Темная и светлая темы** (в будущих версиях)

### 📊 Визуализация данных
- **Интерактивные графики** и диаграммы
- **Карта местоположения** участков
- **Сравнительные таблицы** рыночных цен
- **Рекомендации** по повышению ликвидности

## Технологический стек

### Frontend
- **React 18** - Библиотека для создания пользовательских интерфейсов
- **TypeScript** - Типизированный JavaScript
- **Next.js 14** - Фреймворк для React приложений
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Управление состоянием и кэширование данных
- **React Hook Form** - Управление формами
- **Zod** - Валидация данных
- **Lucide React** - Иконки
- **React Hot Toast** - Уведомления

### Архитектура
- **Component-based architecture** - Модульная структура компонентов
- **Type-safe API calls** - Типизированные запросы к API
- **State management** - Управление состоянием приложения
- **Error boundaries** - Обработка ошибок
- **Loading states** - Индикаторы загрузки

## Структура проекта

```
frontend/
├── src/
│   ├── components/          # Компоненты приложения
│   │   ├── ParcelSearch.tsx     # Поиск участков
│   │   ├── EvaluationForm.tsx   # Форма оценки
│   │   ├── ResultsDisplay.tsx   # Отображение результатов
│   │   ├── MarketAnalytics.tsx  # Рыночная аналитика
│   │   └── ...
│   ├── pages/               # Страницы приложения
│   │   ├── _app.tsx         # Главное приложение
│   │   ├── index.tsx        # Главная страница
│   │   └── ...
│   ├── styles/              # Стили приложения
│   │   └── globals.css      # Глобальные стили
│   └── types/               # TypeScript типы
├── public/                  # Статические файлы
├── package.json             # Зависимости
├── tsconfig.json            # Конфигурация TypeScript
└── Dockerfile              # Docker образ
```

## Запуск приложения

### Локальная разработка

1. **Установка зависимостей:**
   ```bash
   cd frontend
   npm install
   ```

2. **Запуск в режиме разработки:**
   ```bash
   npm run dev
   ```

3. **Приложение будет доступно по адресу:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

### Docker

1. **Сборка и запуск:**
   ```bash
   docker-compose up -d frontend
   ```

2. **Приложение будет доступно по адресу:**
   - Frontend: http://localhost
   - API: http://localhost:8000

### Production

1. **Сборка production версии:**
   ```bash
   npm run build
   ```

2. **Запуск production версии:**
   ```bash
   npm start
   ```

## Конфигурация

### Environment Variables

```bash
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Режим разработки
NODE_ENV=development

# Другие настройки
NEXT_PUBLIC_APP_NAME="Land Liquidity Assessment"
NEXT_PUBLIC_VERSION="1.0.0"
```

### Конфигурация Nginx

Frontend автоматически настроен для работы с Nginx reverse proxy:
- Статические файлы обслуживаются через Nginx
- API запросы проксируются на backend
- Поддержка HTTPS и SSL сертификатов

## API Интеграция

### Основные endpoints

```typescript
// Поиск участка
POST /api/parcels/search
{
  "cadastralNumber": "78:12:0000101:123"
}

// Оценка ликвидности
POST /api/evaluate
{
  "cadastralNumber": "78:12:0000101:123",
  "address": "г. Москва, ул. Примерная, д. 1",
  "area": 1000,
  "category": "Сельхозназначения",
  "purpose": "Для сельскохозяйственного производства"
}

// Получение результатов
GET /api/assessments/{id}
```

### Обработка ошибок

Приложение обрабатывает все типы ошибок:
- Сетевые ошибки
- Ошибки валидации
- Ошибки сервера
- Таймауты запросов

### Кэширование

Используется React Query для:
- Кэширования результатов запросов
- Автоматического обновления данных
- Оптимизации производительности

## Разработка

### Создание компонентов

1. **Новый компонент:**
   ```tsx
   // src/components/MyComponent.tsx
   import React from 'react'
   
   interface MyComponentProps {
     title: string
     data: any[]
   }
   
   export function MyComponent({ title, data }: MyComponentProps) {
     return (
       <div className="my-component">
         <h2>{title}</h2>
         {/* Компонент */}
       </div>
     )
   }
   ```

2. **Использование компонента:**
   ```tsx
   import { MyComponent } from '@/components/MyComponent'
   
   function HomePage() {
     return (
       <div>
         <MyComponent title="Мой компонент" data={[]} />
       </div>
     )
   }
   ```

### Стили

1. **Tailwind CSS классы:**
   ```tsx
   <div className="bg-white rounded-lg shadow-lg p-6">
     <h2 className="text-2xl font-bold text-gray-900">Заголовок</h2>
   </div>
   ```

2. **Кастомные стили:**
   ```css
   /* frontend/styles/globals.css */
   .custom-class {
     @apply bg-gradient-to-r from-blue-500 to-purple-600;
   }
   ```

### Тестирование

1. **Unit тесты:**
   ```bash
   npm test
   ```

2. **E2E тесты:**
   ```bash
   npm run test:e2e
   ```

3. **Покрытие кода:**
   ```bash
   npm run test:coverage
   ```

## Деплоймент

### Production deployment

1. **Сборка образа:**
   ```bash
   docker build -t land-liquidity-frontend .
   ```

2. **Запуск контейнера:**
   ```bash
   docker run -p 80:80 land-liquidity-frontend
   ```

3. **Docker Compose:**
   ```bash
   docker-compose up -d frontend
   ```

### CI/CD

Приложение интегрировано с GitHub Actions:
- Автоматическая сборка
- Тестирование
- Деплоймент в staging и production

## Мониторинг

### Логи

1. **Frontend логи:**
   ```bash
   docker-compose logs frontend
   ```

2. **Browser console:**
   - Откройте DevTools в браузере
   - Перейдите на вкладку Console

### Метрики

1. **React DevTools:**
   - Профилирование производительности
   - Анализ рендеринга

2. **Lighthouse:**
   - Аудит производительности
   - Рекомендации по оптимизации

## Безопасность

### Защита данных

- **HTTPS** для всех запросов
- **CORS** настройки
- **CSRF** защита
- **Input validation** на frontend и backend

### Аутентификация

- **JWT токены** для авторизации
- **Session management**
- **Role-based access**

## Поддержка

### Troubleshooting

1. **Приложение не запускается:**
   ```bash
   # Проверка логов
   docker-compose logs frontend
   
   # Пересборка
   docker-compose build frontend
   ```

2. **API не доступен:**
   ```bash
   # Проверка backend
   curl http://localhost:8000/health
   
   # Проверка сети
   docker-compose ps
   ```

3. **Проблемы с зависимостями:**
   ```bash
   # Очистка и переустановка
   rm -rf node_modules package-lock.json
   npm install
   ```

### Контакты

- **Email:** support@landliquidity.com
- **Telegram:** @land_liquidity_support
- **Documentation:** [API Docs](http://localhost:8000/docs)

## Лицензия

Этот проект лицензирован в соответствии с MIT License - подробности см. в файле LICENSE.

## Вклад в развитие

Мы приветствуем вклад в развитие проекта!

1. **Fork** репозитория
2. Создайте **feature branch**
3. Сделайте **commit** изменений
4. **Push** в ветку
5. Создайте **Pull Request**

### Требования к коду

- TypeScript для типобезопасности
- ESLint для linting
- Prettier для форматирования
- Тесты для нового функционала