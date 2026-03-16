"""
Celery приложение для фоновых задач
"""

from celery import Celery
from celery.schedules import crontab
import os

# Настройка Celery
celery_app = Celery(
    'land_liquidity',
    broker=os.getenv('RABBITMQ_URL', 'amqp://guest@localhost//'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    task_routes={
        'src.tasks.data_tasks.*': {'queue': 'data'},
        'src.tasks.ml_tasks.*': {'queue': 'ml'},
        'src.tasks.feature_tasks.*': {'queue': 'features'},
    },
    task_default_queue='default',
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Периодические задачи
celery_app.conf.beat_schedule = {
    'update-market-data': {
        'task': 'src.tasks.data_tasks.update_market_data',
        'schedule': crontab(hour=2, minute=0),  # Каждую ночь в 2:00
    },
    'update-infrastructure-data': {
        'task': 'src.tasks.data_tasks.update_infrastructure_data',
        'schedule': crontab(hour=3, minute=0, day_of_week='sunday'),  # Раз в неделю
    },
    'retrain-models': {
        'task': 'src.tasks.ml_tasks.retrain_models',
        'schedule': crontab(hour=4, minute=0, day_of_month='1'),  # Первого числа каждого месяца
    },
    'cleanup-old-data': {
        'task': 'src.tasks.data_tasks.cleanup_old_data',
        'schedule': crontab(hour=1, minute=0, day_of_week='saturday'),  # Каждую субботу
    },
}