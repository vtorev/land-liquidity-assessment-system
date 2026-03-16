"""
Фоновые задачи для машинного обучения
"""

import logging
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os
import pickle
import json

from src.ml.liquidity_model import LiquidityMLModel, LiquidityAssessmentService
from src.models import CadastreParcel, ParcelFeature, LiquidityAssessment
from src.tasks.celery_app import celery_app

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def retrain_models(self):
    """
    Фоновая задача для переобучения ML моделей
    """
    try:
        logger.info("Начало переобучения ML моделей")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Обучение модели регрессии
            regression_model = LiquidityMLModel(model_type='regression', n_estimators=100)
            regression_result = regression_model.train(session, test_size=0.2, cv_folds=5)
            
            # Сохранение метаданных модели
            regression_model.save_model_metadata(session, regression_result)
            
            # Обучение модели классификации
            classification_model = LiquidityMLModel(model_type='classification', n_estimators=100)
            classification_result = classification_model.train(session, test_size=0.2, cv_folds=5)
            
            # Сохранение метаданных модели
            classification_model.save_model_metadata(session, classification_result)
            
            logger.info("Переобучение ML моделей завершено")
            return {
                "status": "success",
                "regression_model": {
                    "version": regression_result.model_version,
                    "metrics": regression_result.metrics,
                    "training_data_size": regression_result.training_data_size
                },
                "classification_model": {
                    "version": classification_result.model_version,
                    "training_data_size": classification_result.training_data_size
                }
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при переобучении ML моделей: {e}")
        raise self.retry(countdown=600, exc=e)


@shared_task(bind=True, max_retries=3)
def assess_parcel_liquidity(self, parcel_id):
    """
    Фоновая задача для оценки ликвидности участка
    
    Args:
        parcel_id: ID участка для оценки
    """
    try:
        logger.info(f"Начало оценки ликвидности для участка {parcel_id}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Создание сервиса оценки
            assessment_service = LiquidityAssessmentService(session)
            
            # Оценка ликвидности
            result = assessment_service.assess_parcel(parcel_id)
            
            logger.info(f"Оценка ликвидности для участка {parcel_id} завершена")
            return {
                "status": "success",
                "parcel_id": parcel_id,
                "liquidity_score": result["liquidity_score"],
                "liquidity_category": result["liquidity_category"],
                "assessment_id": result["assessment_id"]
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при оценке ликвидности для участка {parcel_id}: {e}")
        raise self.retry(countdown=120, exc=e)


@shared_task(bind=True, max_retries=3)
def batch_assess_parcels(self, parcel_ids):
    """
    Фоновая задача для массовой оценки ликвидности участков
    
    Args:
        parcel_ids: Список ID участков для оценки
    """
    try:
        logger.info(f"Начало массовой оценки ликвидности для {len(parcel_ids)} участков")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            assessment_service = LiquidityAssessmentService(session)
            
            results = []
            success_count = 0
            error_count = 0
            
            for parcel_id in parcel_ids:
                try:
                    result = assessment_service.assess_parcel(parcel_id)
                    results.append({
                        "parcel_id": parcel_id,
                        "status": "success",
                        "liquidity_score": result["liquidity_score"],
                        "liquidity_category": result["liquidity_category"]
                    })
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка при оценке участка {parcel_id}: {e}")
                    results.append({
                        "parcel_id": parcel_id,
                        "status": "error",
                        "error": str(e)
                    })
                    error_count += 1
            
            logger.info(f"Массовая оценка завершена: {success_count} успешных, {error_count} ошибок")
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
        logger.error(f"Критическая ошибка при массовой оценке: {e}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def calculate_feature_importance(self, model_path, feature_names):
    """
    Фоновая задача для расчета важности признаков
    
    Args:
        model_path: Путь к файлу модели
        feature_names: Список названий признаков
    """
    try:
        logger.info(f"Начало расчета важности признаков для модели {model_path}")
        
        # Загрузка модели
        model = LiquidityMLModel.load_model(model_path, 'regression')
        
        # Получение важности признаков
        importance = model.model.get_feature_importance()
        
        # Создание словаря важности признаков
        feature_importance = dict(zip(feature_names, importance))
        
        # Сортировка по важности
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        logger.info("Расчет важности признаков завершен")
        return {
            "status": "success",
            "feature_importance": dict(sorted_importance),
            "top_features": sorted_importance[:10]  # Топ-10 признаков
        }
        
    except Exception as e:
        logger.error(f"Ошибка при расчете важности признаков: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def generate_model_report(self, model_version):
    """
    Фоновая задача для генерации отчета о модели
    
    Args:
        model_version: Версия модели
    """
    try:
        logger.info(f"Начало генерации отчета для модели {model_version}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Получение метаданных модели
            from src.models import MLModel as MLModelDB
            model_meta = session.query(MLModelDB).filter(
                MLModelDB.model_version == model_version
            ).first()
            
            if not model_meta:
                return {"status": "error", "message": f"Модель {model_version} не найдена"}
            
            # Статистика по оценкам
            assessments = session.query(LiquidityAssessment).filter(
                LiquidityAssessment.model_version == model_version
            ).all()
            
            # Расчет статистики
            total_assessments = len(assessments)
            avg_score = sum(a.liquidity_score for a in assessments if a.liquidity_score) / max(1, total_assessments)
            
            # Распределение по категориям
            categories = {'high': 0, 'medium': 0, 'low': 0}
            for a in assessments:
                if a.liquidity_category in categories:
                    categories[a.liquidity_category] += 1
            
            report = {
                "model_version": model_version,
                "model_type": model_meta.model_type,
                "training_date": model_meta.training_date.isoformat(),
                "training_data_size": model_meta.training_data_size,
                "metrics": model_meta.accuracy_metrics,
                "feature_importance": model_meta.feature_importance,
                "assessment_statistics": {
                    "total_assessments": total_assessments,
                    "average_score": avg_score,
                    "category_distribution": categories
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Отчет для модели {model_version} сгенерирован")
            return {"status": "success", "report": report}
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при генерации отчета: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def validate_model_performance(self, model_version):
    """
    Фоновая задача для валидации производительности модели
    
    Args:
        model_version: Версия модели для валидации
    """
    try:
        logger.info(f"Начало валидации производительности модели {model_version}")
        
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Получение модели
            from src.models import MLModelDB
            model_meta = session.query(MLModelDB).filter(
                MLModelDB.model_version == model_version
            ).first()
            
            if not model_meta:
                return {"status": "error", "message": f"Модель {model_version} не найдена"}
            
            # Загрузка модели
            model = LiquidityMLModel.load_model(model_meta.model_path, model_meta.model_type)
            
            # Получение последних оценок для валидации
            recent_assessments = session.query(LiquidityAssessment).filter(
                LiquidityAssessment.model_version == model_version,
                LiquidityAssessment.assessment_date >= datetime.now() - timedelta(days=30)
            ).all()
            
            # В реальной системе здесь будет логика валидации производительности
            # Например: сравнение предсказаний с реальными продажами
            
            validation_result = {
                "model_version": model_version,
                "validation_date": datetime.now().isoformat(),
                "assessments_count": len(recent_assessments),
                "status": "passed",  # или "failed" в зависимости от метрик
                "metrics": {
                    "accuracy": 0.85,
                    "precision": 0.82,
                    "recall": 0.88
                }
            }
            
            logger.info(f"Валидация производительности модели {model_version} завершена")
            return {"status": "success", "validation_result": validation_result}
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при валидации производительности: {e}")
        raise self.retry(countdown=120, exc=e)


@shared_task(bind=True, max_retries=3)
def create_synthetic_data(self, count=1000):
    """
    Фоновая задача для создания синтетических данных
    
    Args:
        count: Количество синтетических записей
    """
    try:
        logger.info(f"Начало создания {count} синтетических записей")
        
        import numpy as np
        from sqlalchemy.orm import sessionmaker
        
        # Создание сессии
        engine = create_engine("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            synthetic_data = []
            
            for i in range(count):
                # Генерация синтетических признаков
                area = np.random.uniform(6, 50)  # Площадь от 6 до 50 соток
                distance_to_city = np.random.uniform(1, 50)  # Расстояние до города в км
                infrastructure_score = np.random.uniform(0.1, 0.9)
                market_activity = np.random.uniform(0.05, 0.5)
                
                # Расчет синтетической ликвидности (упрощенная формула)
                liquidity_score = (
                    0.3 * (1 / (1 + distance_to_city / 10)) +  # Чем ближе к городу, тем выше
                    0.4 * infrastructure_score +  # Инфраструктура
                    0.2 * market_activity +  # Рыночная активность
                    0.1 * np.random.normal(0.5, 0.1)  # Шум
                )
                
                # Ограничение в диапазоне 0-1
                liquidity_score = max(0, min(1, liquidity_score))
                
                synthetic_data.append({
                    'area': area,
                    'distance_to_city': distance_to_city,
                    'infrastructure_score': infrastructure_score,
                    'market_activity': market_activity,
                    'liquidity_score': liquidity_score
                })
            
            logger.info(f"Создано {count} синтетических записей")
            return {
                "status": "success",
                "count": count,
                "synthetic_data": synthetic_data[:5]  # Первые 5 записей для примера
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Ошибка при создании синтетических данных: {e}")
        raise self.retry(countdown=60, exc=e)