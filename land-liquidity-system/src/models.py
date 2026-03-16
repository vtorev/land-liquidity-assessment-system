"""
SQLAlchemy модели для системы оценки ликвидности земельных участков
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

Base = declarative_base()


class CadastreParcel(Base):
    """Модель кадастрового участка"""
    __tablename__ = 'cadastre_parcel'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cadastral_number = Column(String(100), unique=True, nullable=False, index=True)
    cadastral_block = Column(String(50))
    area = Column(DECIMAL(15, 3))  # площадь в квадратных метрах
    area_unit = Column(String(20))  # единица измерения площади
    status = Column(String(50))  # действующий, анулирован и т.д.
    category = Column(String(100))  # категория земель
    permitted_use = Column(String(200))  # вид разрешенного использования
    address = Column(Text)
    coordinates = Column(Geometry('POLYGON', srid=4326))  # границы участка в WGS84
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(50))  # источник данных
    source_id = Column(String(100))  # идентификатор в источнике
    
    # Связи
    features = relationship("ParcelFeature", back_populates="parcel", cascade="all, delete-orphan")
    distances = relationship("ParcelDistance", back_populates="parcel", cascade="all, delete-orphan")
    market_listings = relationship("MarketListing", back_populates="parcel", cascade="all, delete-orphan")
    assessments = relationship("LiquidityAssessment", back_populates="parcel", cascade="all, delete-orphan")
    satellite_data = relationship("SatelliteData", back_populates="parcel", cascade="all, delete-orphan")


class ParcelFeature(Base):
    """Модель признаков участка (рассчитанные метрики)"""
    __tablename__ = 'parcel_features'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(Integer, ForeignKey('cadastre_parcel.id', ondelete='CASCADE'), nullable=False)
    feature_type = Column(String(50), nullable=False)  # тип признака
    feature_name = Column(String(100), nullable=False)  # название признака
    feature_value = Column(DECIMAL(15, 6))  # числовое значение
    feature_text = Column(Text)  # текстовое значение (если применимо)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_method = Column(String(100))  # метод расчета
    
    # Связи
    parcel = relationship("CadastreParcel", back_populates="features")
    
    __table_args__ = (
        # Уникальный индекс по parcel_id, feature_type, feature_name
        Index('idx_parcel_features_unique', parcel_id, feature_type, feature_name, unique=True),
    )


class InfrastructureObject(Base):
    """Модель инфраструктурных объектов"""
    __tablename__ = 'infrastructure_objects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    object_type = Column(String(50), nullable=False)  # тип объекта (дорога, школа и т.д.)
    object_subtype = Column(String(100))  # подтип (шоссе, улица и т.д.)
    name = Column(String(200))  # название
    address = Column(Text)
    coordinates = Column(Geometry('POINT', srid=4326))  # координаты объекта
    attributes = Column(JSONB)  # дополнительные атрибуты в JSON
    source = Column(String(50))  # источник данных
    source_id = Column(String(100))  # идентификатор в источнике
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    distances = relationship("ParcelDistance", back_populates="infrastructure_object")


class ParcelDistance(Base):
    """Модель расстояний от участков до объектов инфраструктуры"""
    __tablename__ = 'parcel_distances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(Integer, ForeignKey('cadastre_parcel.id', ondelete='CASCADE'), nullable=False)
    object_id = Column(Integer, ForeignKey('infrastructure_objects.id', ondelete='CASCADE'), nullable=False)
    object_type = Column(String(50))
    distance_meters = Column(DECIMAL(10, 2))  # расстояние в метрах
    travel_time_seconds = Column(DECIMAL(10, 2))  # время в пути в секундах
    travel_method = Column(String(20))  # способ передвижения (пешком, на авто)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    parcel = relationship("CadastreParcel", back_populates="distances")
    infrastructure_object = relationship("InfrastructureObject", back_populates="distances")
    
    __table_args__ = (
        # Уникальный индекс по parcel_id, object_id, travel_method
        Index('idx_parcel_distances_unique', parcel_id, object_id, travel_method, unique=True),
    )


class MarketListing(Base):
    """Модель рыночных данных (объявлений о продаже)"""
    __tablename__ = 'market_listings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(Integer, ForeignKey('cadastre_parcel.id', ondelete='SET NULL'))
    listing_type = Column(String(20))  # продажа, аренда
    price = Column(DECIMAL(15, 2))  # цена
    price_per_unit = Column(DECIMAL(15, 2))  # цена за единицу площади
    price_currency = Column(String(10))  # валюта
    area = Column(DECIMAL(15, 3))  # площадь
    area_unit = Column(String(20))
    listing_date = Column(DateTime)
    status = Column(String(30))  # активно, продано, снято
    source = Column(String(50))  # источник (авито, циан и т.д.)
    source_url = Column(Text)
    source_id = Column(String(100))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    parcel = relationship("CadastreParcel", back_populates="market_listings")


class LiquidityAssessment(Base):
    """Модель оценок ликвидности"""
    __tablename__ = 'liquidity_assessments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(Integer, ForeignKey('cadastre_parcel.id', ondelete='CASCADE'), nullable=False)
    assessment_date = Column(DateTime, default=datetime.utcnow)
    liquidity_score = Column(DECIMAL(5, 4))  # индекс ликвидности 0-1
    liquidity_category = Column(String(20))  # категория (высокая, средняя, низкая)
    predicted_price = Column(DECIMAL(15, 2))  # прогнозируемая цена
    confidence_interval_lower = Column(DECIMAL(15, 2))  # нижняя граница доверительного интервала
    confidence_interval_upper = Column(DECIMAL(15, 2))  # верхняя граница доверительного интервала
    model_version = Column(String(50))  # версия модели
    features_used = Column(JSONB)  # использованные признаки
    assessment_method = Column(String(50))  # метод оценки
    
    # Связи
    parcel = relationship("CadastreParcel", back_populates="assessments")
    factors = relationship("AssessmentFactor", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentFactor(Base):
    """Модель факторов, влияющих на оценку (для Explainable AI)"""
    __tablename__ = 'assessment_factors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey('liquidity_assessments.id', ondelete='CASCADE'), nullable=False)
    feature_name = Column(String(100))
    feature_value = Column(DECIMAL(15, 6))
    feature_importance = Column(DECIMAL(10, 6))  # вклад признака в оценку
    factor_direction = Column(String(10))  # positive, negative
    factor_description = Column(Text)  # текстовое описание влияния
    
    # Связи
    assessment = relationship("LiquidityAssessment", back_populates="factors")


class SatelliteData(Base):
    """Модель спутниковых данных и индексов"""
    __tablename__ = 'satellite_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(Integer, ForeignKey('cadastre_parcel.id', ondelete='CASCADE'), nullable=False)
    date_acquired = Column(DateTime)
    satellite_source = Column(String(50))  # Sentinel, Landsat и т.д.
    ndvi = Column(DECIMAL(6, 4))  # Normalized Difference Vegetation Index
    ndwi = Column(DECIMAL(6, 4))  # Normalized Difference Water Index
    ndbi = Column(DECIMAL(6, 4))  # Normalized Difference Built-up Index
    elevation = Column(DECIMAL(8, 2))  # высота над уровнем моря
    slope = Column(DECIMAL(6, 4))  # уклон
    aspect = Column(DECIMAL(6, 4))  # экспозиция склона
    image_url = Column(Text)  # ссылка на снимок
    
    # Связи
    parcel = relationship("CadastreParcel", back_populates="satellite_data")


class SocioEconomicData(Base):
    """Модель социально-экономических показателей районов"""
    __tablename__ = 'socio_economic_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_code = Column(String(20), index=True)  # код района/муниципалитета
    region_name = Column(String(200))
    population = Column(Integer)
    population_density = Column(DECIMAL(10, 2))  # плотность населения
    average_income = Column(DECIMAL(15, 2))
    unemployment_rate = Column(DECIMAL(6, 4))
    crime_rate = Column(DECIMAL(8, 4))
    education_level = Column(DECIMAL(6, 4))
    healthcare_access = Column(DECIMAL(6, 4))
    data_year = Column(Integer, index=True)
    data_source = Column(String(100))


class UserRequest(Base):
    """Модель пользовательских запросов и кэширования"""
    __tablename__ = 'user_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_type = Column(String(50))  # тип запроса
    request_params = Column(JSONB)  # параметры запроса
    result_data = Column(JSONB)  # результат
    cache_key = Column(String(200), index=True)  # ключ кэша
    response_time_ms = Column(Integer)  # время ответа в миллисекундах
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))  # идентификатор пользователя (если есть)


class MLModel(Base):
    """Модель метаданных о моделях машинного обучения"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50))  # CatBoost, LightGBM и т.д.
    training_date = Column(DateTime)
    training_data_size = Column(Integer)
    accuracy_metrics = Column(JSONB)  # метрики качества модели
    feature_importance = Column(JSONB)  # важность признаков
    model_path = Column(Text)  # путь к файлу модели
    is_active = Column(Boolean, default=False)
    
    __table_args__ = (
        # Уникальный индекс по model_name и model_version
        Index('idx_ml_models_unique', 'model_name', 'model_version', unique=True),
    )


class OperationLog(Base):
    """Модель логов операций"""
    __tablename__ = 'operation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String(50))
    operation_status = Column(String(20))  # success, failed, running
    operation_details = Column(JSONB)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(DECIMAL(10, 3))
    error_message = Column(Text)


# Функции для создания индексов
def create_indexes():
    """Создание дополнительных индексов для производительности"""
    from sqlalchemy import Index
    
    # Индексы для геометрических данных
    Index('idx_cadastre_coordinates', CadastreParcel.coordinates, postgresql_using='gist')
    Index('idx_infrastructure_coordinates', InfrastructureObject.coordinates, postgresql_using='gist')
    
    # Индексы для поиска
    Index('idx_parcel_features_search', ParcelFeature.parcel_id, ParcelFeature.feature_type)
    Index('idx_parcel_distances_search', ParcelDistance.parcel_id, ParcelDistance.object_type)
    Index('idx_market_search', MarketListing.parcel_id, MarketListing.listing_date)
    Index('idx_assessment_search', LiquidityAssessment.parcel_id, LiquidityAssessment.assessment_date)
    
    # Индексы для производительности
    Index('idx_assessment_score', LiquidityAssessment.liquidity_score)
    Index('idx_distance_value', ParcelDistance.distance_meters)
    Index('idx_market_price', MarketListing.price)


# Функция для инициализации базы данных
def init_database(engine):
    """Инициализация базы данных - создание таблиц"""
    Base.metadata.create_all(engine)
    create_indexes()