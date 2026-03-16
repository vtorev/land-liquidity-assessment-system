"""
Модуль машинного обучения для оценки ликвидности земельных участков
"""

import logging
import pickle
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, classification_report
import shap
import mlflow
import mlflow.sklearn
from catboost import CatBoostRegressor, CatBoostClassifier, Pool
import joblib

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.sql import text

from src.models import CadastreParcel, ParcelFeature, LiquidityAssessment, MLModel as MLModelDB

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelTrainingResult:
    """Результат обучения модели"""
    model_path: str
    model_version: str
    metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    model_type: str
    training_data_size: int
    cv_scores: List[float]


class LiquidityMLModel:
    """Модель машинного обучения для оценки ликвидности"""
    
    def __init__(self, model_type: str = 'regression', n_estimators: int = 100):
        """
        Инициализация модели
        
        Args:
            model_type: Тип модели ('regression' или 'classification')
            n_estimators: Количество деревьев
        """
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder() if model_type == 'classification' else None
        self.feature_names = []
        self.is_trained = False
        
    def prepare_training_data(self, session: Session) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Подготовка данных для обучения модели
        
        Args:
            session: Сессия SQLAlchemy
            
        Returns:
            Кортеж (признаки, целевая переменная)
        """
        logger.info("Подготовка данных для обучения...")
        
        # Запрос данных из базы данных
        query = session.query(
            CadastreParcel.id,
            CadastreParcel.area,
            ParcelFeature.feature_type,
            ParcelFeature.feature_name,
            ParcelFeature.feature_value,
            LiquidityAssessment.liquidity_score,
            LiquidityAssessment.liquidity_category,
            LiquidityAssessment.predicted_price
        ).join(
            ParcelFeature, CadastreParcel.id == ParcelFeature.parcel_id
        ).join(
            LiquidityAssessment, CadastreParcel.id == LiquidityAssessment.parcel_id
        ).filter(
            LiquidityAssessment.liquidity_score.isnot(None)
        )
        
        # Преобразуем в DataFrame
        data = []
        for row in query.all():
            data.append({
                'parcel_id': row.id,
                'area': row.area,
                'feature_type': row.feature_type,
                'feature_name': row.feature_name,
                'feature_value': row.feature_value,
                'liquidity_score': row.liquidity_score,
                'liquidity_category': row.liquidity_category,
                'predicted_price': row.predicted_price
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            raise ValueError("Нет данных для обучения модели")
        
        # Поворачиваем таблицу (pivot)
        features_df = df.pivot_table(
            index='parcel_id',
            columns='feature_name',
            values='feature_value',
            aggfunc='first'
        ).reset_index()
        
        # Добавляем целевые переменные
        target_df = df[['parcel_id', 'liquidity_score', 'liquidity_category']].drop_duplicates()
        merged_df = features_df.merge(target_df, on='parcel_id', how='inner')
        
        # Заполняем пропущенные значения
        numeric_columns = merged_df.select_dtypes(include=[np.number]).columns
        merged_df[numeric_columns] = merged_df[numeric_columns].fillna(merged_df[numeric_columns].median())
        
        # Отбираем признаки
        feature_columns = [col for col in merged_df.columns if col not in 
                          ['parcel_id', 'liquidity_score', 'liquidity_category', 'predicted_price']]
        
        X = merged_df[feature_columns]
        y = merged_df['liquidity_score'] if self.model_type == 'regression' else merged_df['liquidity_category']
        
        # Сохраняем названия признаков
        self.feature_names = list(X.columns)
        
        logger.info(f"Подготовлено {len(X)} образцов с {len(self.feature_names)} признаками")
        
        return X, y
    
    def train(self, session: Session, test_size: float = 0.2, cv_folds: int = 5) -> ModelTrainingResult:
        """
        Обучение модели
        
        Args:
            session: Сессия SQLAlchemy
            test_size: Размер тестовой выборки
            cv_folds: Количество фолдов для кросс-валидации
            
        Returns:
            Результат обучения
        """
        logger.info("Начало обучения модели...")
        
        # Подготовка данных
        X, y = self.prepare_training_data(session)
        
        # Разделение на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if self.model_type == 'classification' else None
        )
        
        # Обучение модели
        if self.model_type == 'regression':
            self.model = CatBoostRegressor(
                iterations=self.n_estimators,
                learning_rate=0.1,
                depth=6,
                loss_function='RMSE',
                verbose=False,
                random_seed=42
            )
        else:
            self.model = CatBoostClassifier(
                iterations=self.n_estimators,
                learning_rate=0.1,
                depth=6,
                loss_function='MultiClass',
                verbose=False,
                random_seed=42
            )
        
        # Обучение
        train_pool = Pool(X_train, y_train, feature_names=self.feature_names)
        self.model.fit(train_pool)
        
        # Оценка модели
        test_pool = Pool(X_test, y_test, feature_names=self.feature_names)
        y_pred = self.model.predict(test_pool)
        
        # Расчет метрик
        if self.model_type == 'regression':
            metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'mae': mean_absolute_error(y_test, y_pred),
                'r2': r2_score(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred))
            }
        else:
            metrics = {
                'classification_report': classification_report(y_test, y_pred, output_dict=True)
            }
        
        # Кросс-валидация
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=cv_folds, scoring='r2' if self.model_type == 'regression' else 'accuracy')
        
        # Важность признаков
        feature_importance = dict(zip(self.feature_names, self.model.get_feature_importance()))
        
        # Сохранение модели
        model_version = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = f"models/liquidity_model_{self.model_type}_{model_version}.pkl"
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        
        self.is_trained = True
        
        result = ModelTrainingResult(
            model_path=model_path,
            model_version=model_version,
            metrics=metrics,
            feature_importance=feature_importance,
            model_type=self.model_type,
            training_data_size=len(X),
            cv_scores=list(cv_scores)
        )
        
        logger.info(f"Модель обучена. Версия: {model_version}")
        logger.info(f"Метрики: {metrics}")
        
        return result
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        Предсказание ликвидности
        
        Args:
            features: Признаки участка
            
        Returns:
            Предсказание
        """
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        
        # Проверка соответствия признаков
        missing_features = set(self.feature_names) - set(features.columns)
        if missing_features:
            raise ValueError(f"Отсутствуют признаки: {missing_features}")
        
        # Выбор только нужных признаков в правильном порядке
        X = features[self.feature_names]
        
        # Заполнение пропущенных значений
        X = X.fillna(X.median())
        
        # Предсказание
        pool = Pool(X, feature_names=self.feature_names)
        predictions = self.model.predict(pool)
        
        return predictions
    
    def explain_prediction(self, features: pd.DataFrame, parcel_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Объяснение предсказания с помощью SHAP
        
        Args:
            features: Признаки участка
            parcel_id: ID участка (опционально)
            
        Returns:
            Объяснение предсказания
        """
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        
        # Подготовка данных
        X = features[self.feature_names].fillna(0)
        pool = Pool(X, feature_names=self.feature_names)
        
        # Расчет SHAP значений
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(pool)
        
        # Формирование результата
        explanation = {
            'parcel_id': parcel_id,
            'prediction': float(self.model.predict(pool)[0]) if len(pool.data) == 1 else self.model.predict(pool).tolist(),
            'base_value': float(explainer.expected_value),
            'shap_values': dict(zip(self.feature_names, shap_values[0] if len(shap_values.shape) > 1 else shap_values)),
            'feature_importance': dict(zip(self.feature_names, self.model.get_feature_importance())),
            'timestamp': datetime.now().isoformat()
        }
        
        return explanation
    
    def save_model_metadata(self, session: Session, result: ModelTrainingResult) -> bool:
        """
        Сохранение метаданных модели в базу данных
        
        Args:
            session: Сессия SQLAlchemy
            result: Результат обучения
            
        Returns:
            Успешность сохранения
        """
        try:
            # Проверка, есть ли уже активная модель этого типа
            existing_active = session.query(MLModelDB).filter(
                and_(
                    MLModelDB.model_type == self.model_type,
                    MLModelDB.is_active == True
                )
            ).first()
            
            if existing_active:
                existing_active.is_active = False
            
            # Создание новой записи
            ml_model = MLModelDB(
                model_name=f'liquidity_{self.model_type}',
                model_version=result.model_version,
                model_type=self.model_type,
                training_date=datetime.now(),
                training_data_size=result.training_data_size,
                accuracy_metrics=result.metrics,
                feature_importance=result.feature_importance,
                model_path=result.model_path,
                is_active=True
            )
            
            session.add(ml_model)
            session.commit()
            
            logger.info(f"Метаданные модели сохранены: {result.model_version}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения метаданных модели: {e}")
            return False
    
    @classmethod
    def load_model(cls, model_path: str, model_type: str) -> 'LiquidityMLModel':
        """
        Загрузка сохраненной модели
        
        Args:
            model_path: Путь к файлу модели
            model_type: Тип модели
            
        Returns:
            Загруженная модель
        """
        model = cls(model_type=model_type)
        model.model = joblib.load(model_path)
        model.is_trained = True
        
        # Загрузка названий признаков из имени файла или дополнительного файла
        # В реальной системе признаки можно сохранять вместе с моделью
        logger.info(f"Модель загружена из {model_path}")
        
        return model
    
    def hyperparameter_tuning(self, session: Session, param_grid: Dict[str, List], cv_folds: int = 3) -> Dict:
        """
        Подбор гиперпараметров
        
        Args:
            session: Сессия SQLAlchemy
            param_grid: Сетка параметров для перебора
            cv_folds: Количество фолдов для кросс-валидации
            
        Returns:
            Лучшие параметры
        """
        logger.info("Начало подбора гиперпараметров...")
        
        X, y = self.prepare_training_data(session)
        
        if self.model_type == 'regression':
            base_model = CatBoostRegressor(verbose=False, random_seed=42)
            scoring = 'neg_mean_squared_error'
        else:
            base_model = CatBoostClassifier(verbose=False, random_seed=42)
            scoring = 'accuracy'
        
        # Поиск лучших параметров
        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            scoring=scoring,
            cv=cv_folds,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        logger.info(f"Лучшие параметры: {grid_search.best_params_}")
        logger.info(f"Лучшая оценка: {grid_search.best_score_}")
        
        return grid_search.best_params_


class LiquidityAssessmentService:
    """Сервис для оценки ликвидности участков"""
    
    def __init__(self, session: Session, model_path: Optional[str] = None, model_type: str = 'regression'):
        """
        Инициализация сервиса
        
        Args:
            session: Сессия SQLAlchemy
            model_path: Путь к модели (если None - загружается активная модель из БД)
            model_type: Тип модели
        """
        self.session = session
        self.model_type = model_type
        
        if model_path:
            self.model = LiquidityMLModel.load_model(model_path, model_type)
        else:
            self.model = self._load_active_model()
    
    def _load_active_model(self) -> LiquidityMLModel:
        """Загрузка активной модели из базы данных"""
        active_model = self.session.query(MLModelDB).filter(
            and_(
                MLModelDB.model_type == self.model_type,
                MLModelDB.is_active == True
            )
        ).first()
        
        if not active_model:
            raise ValueError(f"Активная модель типа {self.model_type} не найдена")
        
        return LiquidityMLModel.load_model(active_model.model_path, self.model_type)
    
    def assess_parcel(self, parcel_id: int) -> Dict[str, Any]:
        """
        Оценка ликвидности участка
        
        Args:
            parcel_id: ID участка
            
        Returns:
            Результат оценки
        """
        # Получаем признаки участка
        features = self._get_parcel_features(parcel_id)
        
        if features.empty:
            raise ValueError(f"Признаки для участка {parcel_id} не найдены")
        
        # Предсказание
        prediction = self.model.predict(features)
        
        # Объяснение
        explanation = self.model.explain_prediction(features, parcel_id)
        
        # Сохранение результата
        assessment = LiquidityAssessment(
            parcel_id=parcel_id,
            assessment_date=datetime.now(),
            liquidity_score=float(prediction[0]) if len(prediction) == 1 else float(np.mean(prediction)),
            liquidity_category=self._score_to_category(float(prediction[0])) if self.model_type == 'classification' else None,
            model_version=self.model.model.model_version if hasattr(self.model.model, 'model_version') else 'unknown',
            features_used=features.to_dict('records')[0] if len(features) == 1 else features.to_dict('records'),
            assessment_method='ml_model'
        )
        
        self.session.add(assessment)
        self.session.commit()
        
        result = {
            'parcel_id': parcel_id,
            'liquidity_score': float(prediction[0]) if len(prediction) == 1 else float(np.mean(prediction)),
            'liquidity_category': self._score_to_category(float(prediction[0])) if self.model_type == 'classification' else None,
            'explanation': explanation,
            'assessment_id': assessment.id,
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def _get_parcel_features(self, parcel_id: int) -> pd.DataFrame:
        """Получение признаков участка"""
        features = self.session.query(ParcelFeature).filter(
            ParcelFeature.parcel_id == parcel_id
        ).all()
        
        if not features:
            return pd.DataFrame()
        
        # Формируем DataFrame
        data = {}
        for feature in features:
            data[feature.feature_name] = feature.feature_value
        
        return pd.DataFrame([data])
    
    def _score_to_category(self, score: float) -> str:
        """Преобразование числового балла в категорию"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'


def main():
    """Пример использования ML модели"""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    
    # Подключение к базе данных
    database_url = "postgresql://user:password@localhost:5432/land_liquidity"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Обучение модели
        model = LiquidityMLModel(model_type='regression', n_estimators=50)
        result = model.train(session)
        
        # Сохранение метаданных
        model.save_model_metadata(session, result)
        
        print(f"Модель обучена:")
        print(f"  Версия: {result.model_version}")
        print(f"  Метрики: {result.metrics}")
        print(f"  Размер данных: {result.training_data_size}")
        
        # Оценка участка
        assessment_service = LiquidityAssessmentService(session, result.model_path, 'regression')
        assessment_result = assessment_service.assess_parcel(1)
        
        print(f"\nОценка участка:")
        print(f"  ID: {assessment_result['parcel_id']}")
        print(f"  Индекс ликвидности: {assessment_result['liquidity_score']}")
        print(f"  Объяснение: {assessment_result['explanation']}")
        
    except Exception as e:
        logger.error(f"Ошибка в примере использования: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()