# Инструкция по развертыванию системы оценки ликвидности земельных участков на хостинге Beget

## Содержание

1. [Подготовка к развертыванию](#подготовка-к-развертыванию)
2. [Настройка хостинга Beget](#настройка-хостинга-beget)
3. [Развертывание backend части](#развертывание-backend-части)
4. [Развертывание frontend части](#развертывание-frontend-части)
5. [Настройка базы данных](#настройка-базы-данных)
6. [Настройка веб-сервера](#настройка-веб-сервера)
7. [Запуск и тестирование](#запуск-и-тестирование)
8. [Мониторинг и поддержка](#мониторинг-и-поддержка)

## Подготовка к развертыванию

### 1. Анализ требований

**Система оценки ликвидности земельных участков** требует:

- **Backend**: Python 3.8+, FastAPI, PostgreSQL, Redis
- **Frontend**: Node.js 16+, Next.js, React
- **База данных**: PostgreSQL с PostGIS расширением
- **Кэширование**: Redis
- **Веб-сервер**: Nginx (или Apache)

### 2. Выбор тарифного плана Beget

Для данной системы рекомендуется тариф **"Виртуальный выделенный сервер (VPS)"** или **"Выделенный сервер"**, так как:

- Требуется установка PostgreSQL с PostGIS
- Нужна возможность настройки Redis
- Требуется установка Python и Node.js
- Необходимо настраивать веб-сервер

**Рекомендуемые тарифы:**
- VPS 4: 4 ядра, 8 ГБ RAM, 160 ГБ SSD
- VPS 8: 8 ядер, 16 ГБ RAM, 320 ГБ SSD

### 3. Подготовка проекта

#### Создание production конфигурации
```bash
# Создаем production конфигурацию
mkdir production
cd production

# Копируем production файлы
cp ../.env.example .env.production
cp ../docker-compose.yml docker-compose.production.yml
```

#### Настройка production .env
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_DB=land_liquidity_prod
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_URL=https://your-domain.com

# Frontend
FRONTEND_URL=https://your-domain.com

# Секреты (ОБЯЗАТЕЛЬНО измените!)
SECRET_KEY=your_very_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# ML модели
ML_MODEL_PATH=/app/models/prod_model.pkl

# Логирование
LOG_LEVEL=WARNING
LOG_FORMAT=json

# Безопасность
CORS_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## Настройка хостинга Beget

### 1. Доступ к серверу

#### Подключение по SSH
```bash
# Подключение к серверу
ssh root@your-server-ip

# Или с использованием ключа
ssh -i /path/to/your/private.key root@your-server-ip
```

#### Обновление системы
```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

### 2. Установка необходимых компонентов

#### Установка Python и pip
```bash
# Ubuntu/Debian
apt install python3.9 python3.9-pip python3.9-venv -y

# CentOS/RHEL
yum install python39 python39-pip python39-venv -y

# Проверка установки
python3.9 --version
pip3.9 --version
```

#### Установка Node.js
```bash
# Установка Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Проверка установки
node --version
npm --version
```

#### Установка PostgreSQL с PostGIS
```bash
# Ubuntu/Debian
apt install postgresql postgresql-contrib postgis -y

# CentOS/RHEL
yum install postgresql-server postgresql-contrib postgis -y

# Инициализация PostgreSQL (CentOS)
postgresql-setup initdb

# Запуск и включение автозагрузки
systemctl start postgresql
systemctl enable postgresql
```

#### Установка Redis
```bash
# Ubuntu/Debian
apt install redis-server -y

# CentOS/RHEL
yum install redis -y

# Запуск и включение автозагрузки
systemctl start redis
systemctl enable redis
```

#### Установка Nginx
```bash
# Ubuntu/Debian
apt install nginx -y

# CentOS/RHEL
yum install nginx -y

# Запуск и включение автозагрузки
systemctl start nginx
systemctl enable nginx
```

### 3. Настройка PostgreSQL

#### Создание пользователя и базы данных
```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# Внутри psql выполните:
CREATE DATABASE land_liquidity_prod;
CREATE USER prod_user WITH PASSWORD 'your_secure_password';
ALTER ROLE prod_user SET client_encoding TO 'utf8';
ALTER ROLE prod_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE prod_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE land_liquidity_prod TO prod_user;

# Включение PostGIS расширения
\c land_liquidity_prod
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

# Выход из psql
\q
```

#### Настройка PostgreSQL для внешних подключений
```bash
# Редактирование конфигурации PostgreSQL
nano /etc/postgresql/*/main/postgresql.conf

# Найдите и измените:
listen_addresses = '*'  # вместо 'localhost'
port = 5432

# Редактирование pg_hba.conf
nano /etc/postgresql/*/main/pg_hba.conf

# Добавьте строки:
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5

# Перезагрузка PostgreSQL
systemctl restart postgresql
```

### 4. Настройка Redis

#### Настройка Redis для внешних подключений
```bash
# Редактирование конфигурации Redis
nano /etc/redis/redis.conf

# Найдите и измените:
bind 0.0.0.0  # вместо 127.0.0.1
port 6379
requirepass your_redis_password

# Перезагрузка Redis
systemctl restart redis
```

## Развертывание backend части

### 1. Создание структуры директорий

```bash
# Создание директорий
mkdir -p /var/www/land-liquidity/{backend,logs,models}

# Установка прав
chown -R www-data:www-data /var/www/land-liquidity
chmod -R 755 /var/www/land-liquidity
```

### 2. Копирование backend кода

```bash
# Копирование backend кода на сервер
scp -r src/ root@your-server-ip:/var/www/land-liquidity/backend/src/
scp requirements.txt root@your-server-ip:/var/www/land-liquidity/backend/
scp config/ root@your-server-ip:/var/www/land-liquidity/backend/
```

### 3. Настройка Python окружения

```bash
# Переключение на пользователя www-data
sudo -u www-data bash

# Создание виртуального окружения
cd /var/www/land-liquidity/backend
python3.9 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Установка дополнительных пакетов для production
pip install gunicorn psycopg2-binary redis celery

# Проверка установки
python -c "import sqlalchemy; print('SQLAlchemy installed')"
python -c "import fastapi; print('FastAPI installed')"
python -c "import psycopg2; print('PostgreSQL adapter installed')"
```

### 4. Настройка базы данных

```bash
# Активация виртуального окружения
cd /var/www/land-liquidity/backend
source venv/bin/activate

# Создание таблиц в базе данных
python -c "
from sqlalchemy import create_engine
from src.models import Base

engine = create_engine('postgresql://prod_user:your_password@localhost:5432/land_liquidity_prod')
Base.metadata.create_all(engine)
print('Database tables created successfully')
"

# Проверка подключения
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://prod_user:your_password@localhost:5432/land_liquidity_prod')
connection = engine.connect()
print('Database connection successful')
connection.close()
"
```

### 5. Создание systemd сервиса для backend

```bash
# Создание systemd сервиса
cat > /etc/systemd/system/land-liquidity-backend.service << EOF
[Unit]
Description=Land Liquidity Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/land-liquidity/backend
Environment=PATH=/var/www/land-liquidity/backend/venv/bin
Environment=ENVIRONMENT=production
Environment=DATABASE_URL=postgresql://prod_user:your_password@localhost:5432/land_liquidity_prod
Environment=REDIS_URL=redis://localhost:6379/0
Environment=CELERY_BROKER_URL=redis://localhost:6379/0
Environment=CELERY_RESULT_BACKEND=redis://localhost:6379/0
Environment=SECRET_KEY=your_secret_key
Environment=JWT_SECRET_KEY=your_jwt_secret
ExecStart=/var/www/land-liquidity/backend/venv/bin/gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
systemctl daemon-reload

# Запуск сервиса
systemctl start land-liquidity-backend
systemctl enable land-liquidity-backend

# Проверка статуса
systemctl status land-liquidity-backend
```

### 6. Настройка Celery workers

```bash
# Создание systemd сервиса для Celery workers
cat > /etc/systemd/system/land-liquidity-celery.service << EOF
[Unit]
Description=Land Liquidity Celery Workers
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/land-liquidity/backend
Environment=PATH=/var/www/land-liquidity/backend/venv/bin
Environment=ENVIRONMENT=production
Environment=DATABASE_URL=postgresql://prod_user:your_password@localhost:5432/land_liquidity_prod
Environment=REDIS_URL=redis://localhost:6379/0
Environment=CELERY_BROKER_URL=redis://localhost:6379/0
Environment=CELERY_RESULT_BACKEND=redis://localhost:6379/0
Environment=SECRET_KEY=your_secret_key
Environment=JWT_SECRET_KEY=your_jwt_secret
ExecStart=/var/www/land-liquidity/backend/venv/bin/celery -A src.tasks.celery_app worker --loglevel=info --concurrency=2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Создание systemd сервиса для Celery beat
cat > /etc/systemd/system/land-liquidity-celery-beat.service << EOF
[Unit]
Description=Land Liquidity Celery Beat Scheduler
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/land-liquidity/backend
Environment=PATH=/var/www/land-liquidity/backend/venv/bin
Environment=ENVIRONMENT=production
Environment=DATABASE_URL=postgresql://prod_user:your_password@localhost:5432/land_liquidity_prod
Environment=REDIS_URL=redis://localhost:6379/0
Environment=CELERY_BROKER_URL=redis://localhost:6379/0
Environment=CELERY_RESULT_BACKEND=redis://localhost:6379/0
Environment=SECRET_KEY=your_secret_key
Environment=JWT_SECRET_KEY=your_jwt_secret
ExecStart=/var/www/land-liquidity/backend/venv/bin/celery -A src.tasks.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск сервисов
systemctl daemon-reload
systemctl start land-liquidity-celery
systemctl enable land-liquidity-celery
systemctl start land-liquidity-celery-beat
systemctl enable land-liquidity-celery-beat

# Проверка статуса
systemctl status land-liquidity-celery
systemctl status land-liquidity-celery-beat
```

## Развертывание frontend части

### 1. Создание структуры директорий

```bash
# Создание директорий для frontend
mkdir -p /var/www/land-liquidity/frontend

# Установка прав
chown -R www-data:www-data /var/www/land-liquidity/frontend
chmod -R 755 /var/www/land-liquidity/frontend
```

### 2. Копирование frontend кода

```bash
# Копирование frontend кода на сервер
scp -r frontend/ root@your-server-ip:/var/www/land-liquidity/
```

### 3. Установка зависимостей и сборка

```bash
# Переключение на сервер
ssh root@your-server-ip

# Установка зависимостей и сборка
cd /var/www/land-liquidity/frontend
npm install
npm run build

# Проверка сборки
ls -la /var/www/land-liquidity/frontend/.next/
```

### 4. Настройка Next.js для production

```bash
# Создание production конфигурации
cat > /var/www/land-liquidity/frontend/.env.production << EOF
NEXT_PUBLIC_API_URL=https://your-domain.com
NODE_ENV=production
EOF

# Пересборка с production конфигурацией
npm run build
```

## Настройка базы данных

### 1. Создание резервной копии и восстановление

```bash
# Создание резервной копии (если есть данные)
pg_dump -U prod_user -h localhost land_liquidity_prod > backup.sql

# Восстановление из резервной копии
psql -U prod_user -h localhost -d land_liquidity_prod < backup.sql
```

### 2. Создание индексов для производительности

```bash
# Подключение к базе данных
sudo -u postgres psql -d land_liquidity_prod

# Создание индексов
CREATE INDEX CONCURRENTLY idx_cadastre_parcel_cadastral_number ON cadastre_parcel(cadastral_number);
CREATE INDEX CONCURRENTLY idx_cadastre_parcel_coordinates ON cadastre_parcel USING GIST(coordinates);
CREATE INDEX CONCURRENTLY idx_parcel_features_parcel_id ON parcel_features(parcel_id);
CREATE INDEX CONCURRENTLY idx_parcel_distances_parcel_id ON parcel_distances(parcel_id);
CREATE INDEX CONCURRENTLY idx_market_listings_parcel_id ON market_listings(parcel_id);
CREATE INDEX CONCURRENTLY idx_liquidity_assessments_parcel_id ON liquidity_assessments(parcel_id);

# Выход
\q
```

### 3. Настройка резервного копирования

```bash
# Создание скрипта резервного копирования
cat > /usr/local/bin/backup_database.sh << 'EOF'
#!/bin/bash

# Конфигурация
DB_NAME="land_liquidity_prod"
DB_USER="prod_user"
BACKUP_DIR="/var/backups/land-liquidity"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Создание бэкапа
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Удаление бэкапов старше 7 дней
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Database backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
EOF

# Сделать скрипт исполняемым
chmod +x /usr/local/bin/backup_database.sh

# Добавление в cron (ежедневно в 2:00)
echo "0 2 * * * root /usr/local/bin/backup_database.sh" >> /etc/crontab

# Перезапуск cron
systemctl restart cron
```

## Настройка веб-сервера

### 1. Настройка Nginx

```bash
# Создание конфигурации Nginx
cat > /etc/nginx/sites-available/land-liquidity << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL сертификаты (будут добавлены позже)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # Безопасность
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Логирование
    access_log /var/log/nginx/land-liquidity_access.log;
    error_log /var/log/nginx/land-liquidity_error.log;
    
    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
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
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
    
    # Статические файлы
    location /static/ {
        alias /var/www/land-liquidity/frontend/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Активация конфигурации
ln -s /etc/nginx/sites-available/land-liquidity /etc/nginx/sites-enabled/

# Проверка конфигурации
nginx -t

# Перезагрузка Nginx
systemctl reload nginx
```

### 2. Установка SSL сертификата

#### Вариант 1: Let's Encrypt (рекомендуется)
```bash
# Установка Certbot
apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
certbot --nginx -d your-domain.com -d www.your-domain.com

# Автоматическое обновление
echo "0 12 * * 0 /usr/bin/certbot renew --quiet" >> /etc/crontab
```

#### Вариант 2: Ручная установка сертификата
```bash
# Загрузка сертификата и приватного ключа
# (сертификат должен быть получен от SSL провайдера)

# Редактирование конфигурации Nginx
nano /etc/nginx/sites-available/land-liquidity

# Раскомментировать и указать пути:
# ssl_certificate /path/to/your/certificate.crt;
# ssl_certificate_key /path/to/your/private.key;

# Перезагрузка Nginx
systemctl reload nginx
```

### 3. Настройка firewall

```bash
# Установка UFW
apt install ufw -y

# Настройка правил
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 5432       # PostgreSQL (закрыть от внешнего доступа)
ufw deny 6379       # Redis (закрыть от внешнего доступа)
ufw deny 8000       # Backend (закрыть от внешнего доступа)
ufw deny 3000       # Frontend (закрыть от внешнего доступа)

# Включение firewall
ufw enable

# Проверка статуса
ufw status
```

## Запуск и тестирование

### 1. Запуск всех сервисов

```bash
# Запуск всех сервисов
systemctl start postgresql
systemctl start redis
systemctl start land-liquidity-backend
systemctl start land-liquidity-celery
systemctl start land-liquidity-celery-beat
systemctl start nginx

# Проверка статуса всех сервисов
systemctl status postgresql
systemctl status redis
systemctl status land-liquidity-backend
systemctl status land-liquidity-celery
systemctl status land-liquidity-celery-beat
systemctl status nginx
```

### 2. Тестирование backend API

```bash
# Тестирование backend API
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/docs"

# Тестирование через Nginx
curl -X GET "https://your-domain.com/health"
curl -X GET "https://your-domain.com/api/docs"
```

### 3. Тестирование frontend

```bash
# Проверка доступности frontend
curl -X GET "http://localhost:3000"
curl -X GET "https://your-domain.com"
```

### 4. Тестирование базы данных

```bash
# Тестирование подключения к базе данных
sudo -u postgres psql -d land_liquidity_prod -c "SELECT version();"

# Тестирование PostGIS
sudo -u postgres psql -d land_liquidity_prod -c "SELECT PostGIS_Version();"
```

### 5. Тестирование Redis

```bash
# Тестирование Redis
redis-cli ping
redis-cli -a your_redis_password ping
```

## Мониторинг и поддержка

### 1. Настройка мониторинга

#### Создание скрипта мониторинга
```bash
# Создание скрипта мониторинга
cat > /usr/local/bin/monitor_services.sh << 'EOF'
#!/bin/bash

# Логирование
LOG_FILE="/var/log/land-liquidity-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Функция логирования
log() {
    echo "[$DATE] $1" | tee -a $LOG_FILE
}

# Проверка сервисов
check_service() {
    if systemctl is-active --quiet $1; then
        log "✅ $1 is running"
    else
        log "❌ $1 is not running"
        systemctl start $1
        log "🔄 Restarted $1"
    fi
}

# Проверка сервисов
log "=== Service Status Check ==="
check_service postgresql
check_service redis
check_service land-liquidity-backend
check_service land-liquidity-celery
check_service land-liquidity-celery-beat
check_service nginx

# Проверка дискового пространства
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    log "⚠️  Disk usage is high: ${DISK_USAGE}%"
else
    log "✅ Disk usage is normal: ${DISK_USAGE}%"
fi

# Проверка использования памяти
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
log "📊 Memory usage: ${MEMORY_USAGE}%"

# Проверка нагрузки на CPU
LOAD_AVERAGE=$(uptime | awk -F'load average:' '{print $2}')
log "💻 Load average: $LOAD_AVERAGE"

log "=== End of Check ==="
EOF

# Сделать скрипт исполняемым
chmod +x /usr/local/bin/monitor_services.sh

# Добавление в cron (каждые 15 минут)
echo "*/15 * * * * root /usr/local/bin/monitor_services.sh" >> /etc/crontab

# Перезапуск cron
systemctl restart cron
```

### 2. Настройка логирования

#### Централизованное логирование
```bash
# Создание директории для логов
mkdir -p /var/log/land-liquidity

# Настройка logrotate для backend логов
cat > /etc/logrotate.d/land-liquidity << 'EOF'
/var/log/land-liquidity/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload land-liquidity-backend
    endscript
}
EOF
```

### 3. Резервное копирование

#### Автоматическое резервное копирование
```bash
# Создание скрипта полного резервного копирования
cat > /usr/local/bin/full_backup.sh << 'EOF'
#!/bin/bash

# Конфигурация
BACKUP_DIR="/var/backups/land-liquidity"
DATE=$(date +%Y%m%d_%H%M%S)
DOMAIN="your-domain.com"

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Резервное копирование базы данных
pg_dump -U prod_user -h localhost land_liquidity_prod | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Резервное копирование кода
tar -czf "$BACKUP_DIR/code_backup_$DATE.tar.gz" -C /var/www land-liquidity

# Резервное копирование конфигураций
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
    /etc/nginx/sites-available/land-liquidity \
    /etc/systemd/system/land-liquidity-*.service \
    /etc/postgresql/*/main/postgresql.conf \
    /etc/postgresql/*/main/pg_hba.conf \
    /etc/redis/redis.conf

# Резервное копирование SSL сертификатов
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    tar -czf "$BACKUP_DIR/ssl_backup_$DATE.tar.gz" /etc/letsencrypt/live/$DOMAIN
fi

# Удаление бэкапов старше 30 дней
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Логирование
echo "[$(date)] Full backup completed: $BACKUP_DIR/*_$DATE.*" >> /var/log/land-liquidity/backup.log

# Отправка уведомления (если настроено)
# echo "Backup completed successfully" | mail -s "Land Liquidity Backup" admin@your-domain.com
EOF

# Сделать скрипт исполняемым
chmod +x /usr/local/bin/full_backup.sh

# Добавление в cron (еженедельно в воскресенье в 3:00)
echo "0 3 * * 0 root /usr/local/bin/full_backup.sh" >> /etc/crontab

# Перезапуск cron
systemctl restart cron
```

### 4. Обновление системы

#### Создание скрипта обновления
```bash
# Создание скрипта обновления системы
cat > /usr/local/bin/update_system.sh << 'EOF'
#!/bin/bash

# Логирование
LOG_FILE="/var/log/land-liquidity-update.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[$DATE] $1" | tee -a $LOG_FILE
}

log "=== System Update Started ==="

# Обновление системы
apt update && apt upgrade -y
log "✅ System packages updated"

# Обновление Python пакетов
source /var/www/land-liquidity/backend/venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r /var/www/land-liquidity/backend/requirements.txt
log "✅ Python packages updated"

# Перезапуск сервисов
systemctl restart land-liquidity-backend
systemctl restart land-liquidity-celery
systemctl restart land-liquidity-celery-beat
systemctl restart nginx
log "✅ Services restarted"

log "=== System Update Completed ==="
EOF

# Сделать скрипт исполняемым
chmod +x /usr/local/bin/update_system.sh
```

## Устранение неполадок

### 1. Распространенные проблемы

#### Проблема: Backend не запускается
```bash
# Проверка логов
journalctl -u land-liquidity-backend -f

# Проверка подключения к базе данных
sudo -u www-data /var/www/land-liquidity/backend/venv/bin/python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://prod_user:password@localhost:5432/land_liquidity_prod'
from sqlalchemy import create_engine
engine = create_engine(os.environ['DATABASE_URL'])
connection = engine.connect()
print('Database connection successful')
connection.close()
"
```

#### Проблема: Frontend не работает
```bash
# Проверка логов Nginx
tail -f /var/log/nginx/land-liquidity_error.log

# Проверка сборки frontend
cd /var/www/land-liquidity/frontend
npm run build
```

#### Проблема: База данных не доступна
```bash
# Проверка статуса PostgreSQL
systemctl status postgresql

# Проверка подключения
sudo -u postgres psql -c "SELECT 1;"

# Проверка конфигурации
cat /etc/postgresql/*/main/pg_hba.conf | grep -E "(host|local)"
```

#### Проблема: Redis не работает
```bash
# Проверка статуса Redis
systemctl status redis

# Проверка подключения
redis-cli ping

# Проверка конфигурации
cat /etc/redis/redis.conf | grep -E "(bind|port|requirepass)"
```

### 2. Восстановление после сбоев

#### Восстановление базы данных из резервной копии
```bash
# Остановка сервисов
systemctl stop land-liquidity-backend
systemctl stop land-liquidity-celery

# Восстановление базы данных
gunzip -c /var/backups/land-liquidity/db_backup_YYYYMMDD_HHMMSS.sql.gz | psql -U prod_user -h localhost land_liquidity_prod

# Запуск сервисов
systemctl start land-liquidity-backend
systemctl start land-liquidity-celery
```

#### Восстановление кода из резервной копии
```bash
# Остановка сервисов
systemctl stop land-liquidity-backend
systemctl stop nginx

# Восстановление кода
tar -xzf /var/backups/land-liquidity/code_backup_YYYYMMDD_HHMMSS.tar.gz -C /var/www/

# Установка зависимостей
cd /var/www/land-liquidity/backend
source venv/bin/activate
pip install -r requirements.txt

# Перезапуск сервисов
systemctl start land-liquidity-backend
systemctl start nginx
```

## Заключение

Развертывание системы оценки ликвидности земельных участков на хостинге Beget требует:

1. **Выбора подходящего тарифа** - VPS или выделенный сервер
2. **Настройки сервера** - установка всех необходимых компонентов
3. **Развертывания backend и frontend** - настройка сервисов и веб-сервера
4. **Настройки базы данных** - PostgreSQL с PostGIS расширением
5. **Настройки безопасности** - firewall, SSL, резервное копирование
6. **Мониторинга и поддержки** - автоматическое наблюдение за системой

**Важные моменты:**
- Все пароли и секреты должны быть изменены на надежные
- Регулярно обновляйте систему и зависимости
- Настройте резервное копирование
- Мониторьте производительность и доступность системы
- Используйте SSL сертификаты для безопасности

**Поддержка:**
- Регулярно проверяйте логи
- Следите за использованием ресурсов
- Обновляйте зависимости
- Тестируйте резервное копирование
- Мониторьте доступность сервисов

Следуя этой инструкции, вы сможете успешно развернуть и поддерживать систему оценки ликвидности земельных участков на хостинге Beget.