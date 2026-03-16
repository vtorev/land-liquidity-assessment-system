"""
Конфигурация приложения
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    app_name: str = "Land Liquidity Assessment API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # База данных
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/land_liquidity", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: str = Field(default="redis_password", env="REDIS_PASSWORD")
    
    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672//", env="RABBITMQ_URL")
    
    # MinIO/S3
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minio_admin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minio_password123", env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    
    # MLflow
    mlflow_tracking_uri: str = Field(default="http://localhost:5001", env="MLFLOW_TRACKING_URI")
    mlflow_s3_endpoint_url: str = Field(default="http://localhost:9000", env="MLFLOW_S3_ENDPOINT_URL")
    
    # OSRM
    osrm_url: str = Field(default="http://localhost:5000", env="OSRM_URL")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # CORS
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")
    
    # Лимиты
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")  # 30 seconds
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    # Безопасность
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, env="JWT_EXPIRATION_MINUTES")  # 24 hours
    
    # Парсинг данных
    rosreestr_base_url: str = Field(default="https://pkk.rosreestr.ru/api", env="ROSREESTR_BASE_URL")
    avito_rate_limit: float = Field(default=2.0, env="AVITO_RATE_LIMIT")
    cian_rate_limit: float = Field(default=1.5, env="CIAN_RATE_LIMIT")
    
    # ML модели
    model_storage_path: str = Field(default="./models", env="MODEL_STORAGE_PATH")
    training_data_path: str = Field(default="./data/training", env="TRAINING_DATA_PATH")
    
    # Мониторинг
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    grafana_url: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DevelopmentSettings(Settings):
    """Настройки для разработки"""
    debug: bool = True
    environment: str = "development"
    database_echo: bool = True


class ProductionSettings(Settings):
    """Настройки для production"""
    debug: bool = False
    environment: str = "production"
    database_echo: bool = False


class TestingSettings(Settings):
    """Настройки для тестирования"""
    debug: bool = True
    environment: str = "testing"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/land_liquidity_test"


def get_settings() -> Settings:
    """Получение настроек в зависимости от окружения"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Глобальный экземпляр настроек
settings = get_settings()