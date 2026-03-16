"""
Фоновые задачи для расчета признаков
"""

import logging
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import time

from src.feature_engineering.feature_calculator import FeatureCalculator, FeatureCalculationResult
from src.models import CadastreParcel, ParcelFeature, ParcelDistance

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def calculate_parcel_features(self, parcel_id):
    """
    Фоновая задача для расчета всех признаков для участка
    
    Args:
        parcel_id: ID участка для расчета признаков
    """
    try:
        logger.info(f"Начало расчета признаков для участка {parcel_id}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            result = calculator.calculate_all_features(parcel_id)
            
            if result.features:
                # Сохранение признаков
                success = calculator.save_features_to_database(parcel_id, result.features)
                
                logger.info(f"Расчет признаков для участка {parcel_id} завершен за {result.calculation_time:.2f} сек")
                return {
                    "status": "success",
                    "parcel_id": parcel_id,
                    "features_count": len(result.features),
                    "calculation_time": result.calculation_time,
                    "errors": result.errors
                }
            else:
                logger.warning(f"Не удалось рассчитать признаки для участка {parcel_id}")
                return {
                    "status": "no_features",
                    "parcel_id": parcel_id,
                    "errors": result.errors
                }
                
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при расчете признаков для участка {parcel_id}: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def calculate_batch_features(self, parcel_ids):
    """
    Фоновая задача для массового расчета признаков
    
    Args:
        parcel_ids: Список ID участков для расчета признаков
    """
    try:
        logger.info(f"Начало массового расчета признаков для {len(parcel_ids)} участков")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            
            results = []
            success_count = 0
            error_count = 0
            
            for parcel_id in parcel_ids:
                try:
                    result = calculator.calculate_all_features(parcel_id)
                    
                    if result.features:
                        success = calculator.save_features_to_database(parcel_id, result.features)
                        results.append({
                            "parcel_id": parcel_id,
                            "status": "success",
                            "features_count": len(result.features),
                            "calculation_time": result.calculation_time
                        })
                        success_count += 1
                    else:
                        results.append({
                            "parcel_id": parcel_id,
                            "status": "no_features",
                            "errors": result.errors
                        })
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Ошибка при расчете признаков для участка {parcel_id}: {e}")
                    results.append({
                        "parcel_id": parcel_id,
                        "status": "error",
                        "error": str(e)
                    })
                    error_count += 1
            
            logger.info(f"Массовый расчет признаков завершен: {success_count} успешных, {error_count} ошибок")
            return {
                "status": "completed",
                "total": len(parcel_ids),
                "success_count": success_count,
                "error_count": error_count,
                "results": results
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Критическая ошибка при массовом расчете признаков: {e}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def calculate_geospatial_features(self, parcel_id):
    """
    Фоновая задача для расчета геопространственных признаков
    
    Args:
        parcel_id: ID участка для расчета геопространственных признаков
    """
    try:
        logger.info(f"Начало расчета геопространственных признаков для участка {parcel_id}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            result = calculator.calculate_geospatial_features(parcel_id)
            
            if result.features:
                # Сохранение геопространственных признаков
                success = calculator.save_features_to_database(parcel_id, result.features)
                
                logger.info(f"Расчет геопространственных признаков для участка {parcel_id} завершен за {result.calculation_time:.2f} сек")
                return {
                    "status": "success",
                    "parcel_id": parcel_id,
                    "features_count": len(result.features),
                    "calculation_time": result.calculation_time,
                    "errors": result.errors
                }
            else:
                logger.warning(f"Не удалось рассчитать геопространственные признаки для участка {parcel_id}")
                return {
                    "status": "no_features",
                    "parcel_id": parcel_id,
                    "errors": result.errors
                }
                
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при расчете геопространственных признаков: {e}")
        raise self.retry(countdown=120, exc=e)


@shared_task(bind=True, max_retries=3)
def calculate_infrastructure_distances(self, parcel_id):
    """
    Фоновая задача для расчета расстояний до объектов инфраструктуры
    
    Args:
        parcel_id: ID участка для расчета расстояний
    """
    try:
        logger.info(f"Начало расчета расстояний до инфраструктуры для участка {parcel_id}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            distances = calculator.calculate_infrastructure_distances(parcel_id)
            
            if distances:
                # Сохранение расстояний
                success = calculator.save_distances_to_database(parcel_id, distances)
                
                logger.info(f"Расчет расстояний до инфраструктуры для участка {parcel_id} завершен")
                return {
                    "status": "success",
                    "parcel_id": parcel_id,
                    "distances_count": len(distances),
                    "distances": distances
                }
            else:
                logger.warning(f"Не удалось рассчитать расстояния для участка {parcel_id}")
                return {
                    "status": "no_distances",
                    "parcel_id": parcel_id
                }
                
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при расчете расстояний до инфраструктуры: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def update_feature_cache(self, feature_type="all"):
    """
    Фоновая задача для обновления кэша признаков
    
    Args:
        feature_type: Тип признаков для обновления кэша
    """
    try:
        logger.info(f"Начало обновления кэша признаков типа: {feature_type}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            
            # В реальной системе здесь будет логика обновления кэша
            # Например: пересчет часто используемых признаков
            
            cache_update_result = {
                "feature_type": feature_type,
                "updated_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            logger.info(f"Кэш признаков типа {feature_type} обновлен")
            return {
                "status": "success",
                "cache_update_result": cache_update_result
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша признаков: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def validate_features(self, parcel_id):
    """
    Фоновая задача для валидации признаков участка
    
    Args:
        parcel_id: ID участка для валидации признаков
    """
    try:
        logger.info(f"Начало валидации признаков для участка {parcel_id}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            validation_result = calculator.validate_features(parcel_id)
            
            logger.info(f"Валидация признаков для участка {parcel_id} завершена")
            return {
                "status": "completed",
                "parcel_id": parcel_id,
                "validation_result": validation_result
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при валидации признаков: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def cleanup_old_features(self, days_old=90):
    """
    Фоновая задача для очистки устаревших признаков
    
    Args:
        days_old: Возраст признаков в днях для удаления
    """
    try:
        logger.info(f"Начало очистки признаков старше {days_old} дней")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # В реальной системе здесь будет логика удаления устаревших признаков
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Пример: удаление старых записей из таблицы признаков
            # deleted_count = session.query(ParcelFeature).filter(
            #     ParcelFeature.created_at < cutoff_date
            # ).delete()
            # session.commit()
            
            cleanup_result = {
                "days_old": days_old,
                "cutoff_date": cutoff_date.isoformat(),
                "status": "completed"
            }
            
            logger.info(f"Очистка устаревших признаков завершена")
            return {
                "status": "success",
                "cleanup_result": cleanup_result
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при очистке устаревших признаков: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def generate_feature_statistics(self, parcel_ids=None):
    """
    Фоновая задача для генерации статистики по признакам
    
    Args:
        parcel_ids: Список ID участков для анализа (если None - анализировать все)
    """
    try:
        logger.info("Начало генерации статистики по признакам")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            calculator = FeatureCalculator(session)
            statistics = calculator.generate_feature_statistics(parcel_ids)
            
            logger.info("Генерация статистики по признакам завершена")
            return {
                "status": "success",
                "statistics": statistics,
                "generated_at": datetime.now().isoformat()
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при генерации статистики по признакам: {e}")
        raise self.retry(countdown=120, exc=e)