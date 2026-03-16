# Dockerfile для frontend приложения
FROM node:18-alpine AS builder

# Установка рабочей директории
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Финальный образ
FROM nginx:alpine

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Копирование собранных файлов
COPY --from=builder /app/dist /usr/share/nginx/html

# Экспорт порта
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]