"""
Модуль для расчета признаков (feature engineering) для оценки ликвидности земельных участков
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import nearest_points
import geopandas as gpd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import requests
import json

from src.models import (
    CadastreParcel, InfrastructureObject, ParcelDistance, 
    ParcelFeature, MarketListing, SatelliteData, SocioEconomicData
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureCalculationResult:
    """Результат расчета признаков"""
    parcel_id: int
    features: Dict[str, Any]
    calculation_time: float
    errors: List[str]


class FeatureCalculator:
    """Класс для расчета признаков участков"""
    
    def __init__(self, session: Session, osrm_url: str = "http://localhost:5000"):
        """
        Инициализация калькулятора признаков
        
        Args:
            session: Сессия SQLAlchemy
            osrm_url: URL сервиса OSRM для маршрутизации
        """
        self.session = session
        self.osrm_url = osrm_url
        
    def calculate_all_features(self, parcel_id: int) -> FeatureCalculationResult:
        """
        Рассчет всех признаков для участка
        
        Args:
            parcel_id: ID участка
            
        Returns:
            Результат расчета признаков
        """
        start_time = datetime.now()
        features = {}
        errors = []
        
        try:
            # Получаем участок из базы данных
            parcel = self.session.query(CadastreParcel).filter(
                CadastreParcel.id == parcel_id
            ).first()
            
            if not parcel:
                raise ValueError(f"Участок с ID {parcel_id} не найден")
            
            # 1. Геометрические признаки
            try:
                geo_features = self._calculate_geometric_features(parcel)
                features.update(geo_features)
            except Exception as e:
                errors.append(f"Ошибка расчета геометрических признаков: {e}")
                logger.error(f"Ошибка геометрических признаков для {parcel_id}: {e}")
            
            # 2. Признаки инфраструктуры
            try:
                infra_features = self._calculate_infrastructure_features(parcel)
                features.update(infra_features)
            except Exception as e:
                errors.append(f"Ошибка расчета признаков инфраструктуры: {e}")
                logger.error(f"Ошибка признаков инфраструктуры для {parcel_id}: {e}")
            
            # 3. Рыночные признаки
            try:
                market_features = self._calculate_market_features(parcel)
                features.update(market_features)
            except Exception as e:
                errors.append(f"Ошибка расчета рыночных признаков: {e}")
                logger.error(f"Ошибка рыночных признаков для {parcel_id}: {e}")
            
            # 4. Спутниковые признаки
            try:
                satellite_features = self._calculate_satellite_features(parcel)
                features.update(satellite_features)
            except Exception as e:
                errors.append(f"Ошибка расчета спутниковых признаков: {e}")
                logger.error(f"Ошибка спутниковых признаков для {parcel_id}: {e}")
            
            # 5. Социально-экономические признаки
            try:
                socio_features = self._calculate_socioeconomic_features(parcel)
                features.update(socio_features)
            except Exception as e:
                errors.append(f"Ошибка расчета социально-экономических признаков: {e}")
                logger.error(f"Ошибка социально-экономических признаков для {parcel_id}: {e}")
            
            # 6. Коммуникации
            try:
                utility_features = self._calculate_utility_features(parcel)
                features.update(utility_features)
            except Exception as e:
                errors.append(f"Ошибка расчета признаков коммуникаций: {e}")
                logger.error(f"Ошибка признаков коммуникаций для {parcel_id}: {e}")
            
        except Exception as e:
            errors.append(f"Критическая ошибка при расчете признаков: {e}")
            logger.error(f"Критическая ошибка для {parcel_id}: {e}")
        
        calculation_time = (datetime.now() - start_time).total_seconds()
        
        return FeatureCalculationResult(
            parcel_id=parcel_id,
            features=features,
            calculation_time=calculation_time,
            errors=errors
        )
    
    def _calculate_geometric_features(self, parcel: CadastreParcel) -> Dict[str, Any]:
        """Расчет геометрических признаков"""
        features = {}
        
        if not parcel.coordinates:
            return features
        
        # Преобразуем геометрию в Shapely объект
        parcel_geom = parcel.coordinates
        
        # 1. Коэффициент формы (чем ближе к 1, тем более правильная форма)
        area = parcel_geom.area
        perimeter = parcel_geom.length
        if perimeter > 0:
            shape_factor = (4 * math.pi * area) / (perimeter ** 2)
            features['shape_factor'] = min(1.0, max(0.0, float(shape_factor)))
        
        # 2. Площадь в сотках
        if area:
            features['area_sotki'] = area / 100
        
        # 3. Периметр в метрах
        if perimeter:
            features['perimeter_meters'] = float(perimeter)
        
        # 4. Центр участка
        centroid = parcel_geom.centroid
        features['centroid_lat'] = centroid.y
        features['centroid_lon'] = centroid.x
        
        # 5. Минимальная описывающая прямоугольная область
        bounds = parcel_geom.bounds  # (minx, miny, maxx, maxy)
        if bounds:
            features['bbox_width'] = bounds[2] - bounds[0]
            features['bbox_height'] = bounds[3] - bounds[1]
            features['bbox_area'] = features['bbox_width'] * features['bbox_height']
        
        # 6. Отношение площади к площади описывающего прямоугольника
        if features.get('bbox_area', 0) > 0:
            features['area_to_bbox_ratio'] = area / features['bbox_area']
        
        return features
    
    def _calculate_infrastructure_features(self, parcel: CadastreParcel) -> Dict[str, Any]:
        """Расчет признаков инфраструктуры"""
        features = {}
        
        if not parcel.coordinates:
            return features
        
        centroid = parcel.coordinates.centroid
        
        # Типы объектов инфраструктуры для анализа
        infrastructure_types = [
            'school', 'kindergarten', 'hospital', 'pharmacy', 'supermarket',
            'mall', 'restaurant', 'cafe', 'gas_station', 'bank', 'atm',
            'park', 'forest', 'lake', 'river', 'highway', 'main_road',
            'public_transport_stop', 'train_station', 'airport'
        ]
        
        for infra_type in infrastructure_types:
            # Получаем ближайшие объекты данного типа
            distances = self._get_nearest_infrastructure_distances(
                centroid, infra_type, limit=5
            )
            
            if distances:
                # Статистика по расстояниям
                distances_array = np.array(distances)
                features[f'{infra_type}_min_distance'] = float(np.min(distances_array))
                features[f'{infra_type}_max_distance'] = float(np.max(distances_array))
                features[f'{infra_type}_avg_distance'] = float(np.mean(distances_array))
                features[f'{infra_type}_count_500m'] = int(np.sum(distances_array <= 500))
                features[f'{infra_type}_count_1000m'] = int(np.sum(distances_array <= 1000))
                features[f'{infra_type}_count_2000m'] = int(np.sum(distances_array <= 2000))
        
        # Расчет времени в пути до города (предполагаем, что центр города в определенных координатах)
        city_center = Point(30.3158, 59.9391)  # Центр Санкт-Петербурга как пример
        try:
            travel_time = self._calculate_travel_time(centroid, city_center, 'driving')
            if travel_time:
                features['travel_time_to_city_center'] = travel_time
        except Exception as e:
            logger.warning(f"Не удалось рассчитать время в пути до центра: {e}")
        
        return features
    
    def _calculate_market_features(self, parcel: CadastreParcel) -> Dict[str, Any]:
        """Расчет рыночных признаков"""
        features = {}
        
        # Получаем рыночные данные за последние 2 года
        two_years_ago = datetime.now() - timedelta(days=730)
        
        market_data = self.session.query(MarketListing).filter(
            and_(
                MarketListing.parcel_id == parcel.id,
                MarketListing.listing_date >= two_years_ago,
                MarketListing.status.in_(['active', 'sold'])
            )
        ).all()
        
        if market_data:
            prices = [ml.price_per_unit for ml in market_data if ml.price_per_unit]
            if prices:
                features['historical_avg_price'] = float(np.mean(prices))
                features['historical_min_price'] = float(np.min(prices))
                features['historical_max_price'] = float(np.max(prices))
                features['historical_price_std'] = float(np.std(prices))
        
        # Анализ рыночной активности в радиусе 5 км
        nearby_listings = self.session.query(MarketListing).join(
            CadastreParcel, MarketListing.parcel_id == CadastreParcel.id
        ).filter(
            and_(
                MarketListing.listing_date >= two_years_ago,
                MarketListing.status == 'active',
                func.ST_Distance(
                    CadastreParcel.coordinates.centroid,
                    parcel.coordinates.centroid
                ) <= 5000  # 5 км
            )
        ).all()
        
        if nearby_listings:
            nearby_prices = [ml.price_per_unit for ml in nearby_listings if ml.price_per_unit]
            if nearby_prices:
                features['nearby_avg_price'] = float(np.mean(nearby_prices))
                features['nearby_listings_count'] = len(nearby_listings)
                features['nearby_price_std'] = float(np.std(nearby_prices))
        
        return features
    
    def _calculate_satellite_features(self, parcel: CadastreParcel) -> Dict[str, Any]:
        """Расчет спутниковых признаков"""
        features = {}
        
        # Получаем последние спутниковые данные
        satellite_data = self.session.query(SatelliteData).filter(
            SatelliteData.parcel_id == parcel.id
        ).order_by(SatelliteData.date_acquired.desc()).first()
        
        if satellite_data:
            if satellite_data.ndvi is not None:
                features['ndvi'] = float(satellite_data.ndvi)
            if satellite_data.ndwi is not None:
                features['ndwi'] = float(satellite_data.ndwi)
            if satellite_data.ndbi is not None:
                features['ndbi'] = float(satellite_data.ndbi)
            if satellite_data.elevation is not None:
                features['elevation'] = float(satellite_data.elevation)
            if satellite_data.slope is not None:
                features['slope'] = float(satellite_data.slope)
            if satellite_data.aspect is not None:
                features['aspect'] = float(satellite_data.aspect)
        
        return features
    
    def _calculate_socioeconomic_features(self, parcel: CadastreParcel) -> Dict[str, Any]:
        """Расчет социально-экономических признаков"""
        features = {}
        
        # Для упрощения предполагаем, что у нас есть код района в адресе
        # В реальной системе нужно будет определять район по координатам
        
        if parcel.address and 'район' in parcel.address.lower():
            # Извлекаем название района из адреса (упрощенный пример)
            import re
            district_match = re.search(r'район\s+([^\s,]+)', parcel.address.lower())
            if district_match:
                district_name = district_match.group(1)
                
                socio_data = self.session.query(SocioEconomicData).filter(
                    SocioEconomicData.region_name.ilike(f'%{district_name}%')
                ).order_by(SocioEconomicData.data_year.desc()).first()
                
                if socio_data:
                    if socio_data.population:
                        features['district_population'] = socio_data.population
                    if socio_data.population_density:
                        features['district_population_density'] = float(socio_data.population_density)
                    if socio_data.average_income:
                        features['district_average_income'] = float(socio_data.average_income)
                    if socio_data.unemployment_rate:
                        features['district_unemployment_rate'] = float(socio_data.unemployment_rate)
                    if socio_data.crime_rate:
                        features['district_crime_rate'] = float(socio_data.crime_rate)
        
        return features
    
    def _calculate_utility_features(self, parcel: CadastreParcel) -> Dict[str, Any]:
        """Расчет признаков коммуникаций"""
        features = {}
        
        if not parcel.coordinates:
            return features
        
        centroid = parcel.coordinates.centroid
        
        # Проверяем наличие коммуникаций по расстоянию до соответствующих объектов
        utility_types = ['power_line', 'gas_pipeline', 'water_pipe', 'sewer_pipe']
        
        for utility_type in utility_types:
            distances = self._get_nearest_infrastructure_distances(
                centroid, utility_type, limit=3
            )
            
            if distances:
                min_distance = min(distances)
                # Если коммуникация в пределах 100 метров, считаем что она есть
                features[f'{utility_type}_available'] = 1 if min_distance <= 100 else 0
                features[f'{utility_type}_distance'] = float(min_distance)
            else:
                features[f'{utility_type}_available'] = 0
                features[f'{utility_type}_distance'] = None
        
        return features
    
    def _get_nearest_infrastructure_distances(
        self, point: Point, infra_type: str, limit: int = 5
    ) -> List[float]:
        """Получение расстояний до ближайших объектов инфраструктуры"""
        distances = []
        
        # Запрос к базе данных для получения объектов инфраструктуры
        objects = self.session.query(InfrastructureObject).filter(
            InfrastructureObject.object_type == infra_type
        ).limit(100).all()  # Ограничиваем для производительности
        
        for obj in objects:
            if obj.coordinates:
                # Рассчитываем расстояние
                obj_point = Point(obj.coordinates.x, obj.coordinates.y)
                distance = point.distance(obj_point) * 111000  # Преобразуем в метры
                distances.append(distance)
        
        # Сортируем и возвращаем первые N значений
        distances.sort()
        return distances[:limit]
    
    def _calculate_travel_time(
        self, point1: Point, point2: Point, method: str = 'driving'
    ) -> Optional[float]:
        """Расчет времени в пути между двумя точками"""
        try:
            # Формируем запрос к OSRM
            coordinates = f"{point1.x},{point1.y};{point2.x},{point2.y}"
            url = f"{self.osrm_url}/route/v1/{method}/{coordinates}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'routes' in data and data['routes']:
                # Время в пути в секундах
                return data['routes'][0]['duration']
            
        except Exception as e:
            logger.warning(f"Ошибка при расчете времени в пути: {e}")
        
        return None
    
    def save_features_to_database(
        self, parcel_id: int, features: Dict[str, Any], calculation_method: str = 'automated'
    ) -> bool:
        """Сохранение рассчитанных признаков в базу данных"""
        try:
            # Удаляем старые признаки для данного типа расчета
            self.session.query(ParcelFeature).filter(
                and_(
                    ParcelFeature.parcel_id == parcel_id,
                    ParcelFeature.calculation_method == calculation_method
                )
            ).delete()
            
            # Сохраняем новые признаки
            for feature_name, feature_value in features.items():
                if feature_value is not None:
                    # Определяем тип признака по названию
                    if 'distance' in feature_name or 'time' in feature_name:
                        feature_type = 'distance'
                    elif 'price' in feature_name or 'cost' in feature_name:
                        feature_type = 'market'
                    elif 'area' in feature_name or 'perimeter' in feature_name:
                        feature_type = 'geometric'
                    elif 'ndvi' in feature_name or 'elevation' in feature_name:
                        feature_type = 'satellite'
                    elif 'population' in feature_name or 'income' in feature_name:
                        feature_type = 'socioeconomic'
                    else:
                        feature_type = 'other'
                    
                    # Определяем тип значения
                    if isinstance(feature_value, str):
                        feature_text = str(feature_value)
                        feature_value = None
                    else:
                        feature_text = None
                        feature_value = float(feature_value) if feature_value is not None else None
                    
                    feature = ParcelFeature(
                        parcel_id=parcel_id,
                        feature_type=feature_type,
                        feature_name=feature_name,
                        feature_value=feature_value,
                        feature_text=feature_text,
                        calculation_method=calculation_method
                    )
                    
                    self.session.add(feature)
            
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Ошибка сохранения признаков для {parcel_id}: {e}")
            return False


def main():
    """Пример использования калькулятора признаков"""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    
    # Пример подключения к базе данных
    database_url = "postgresql://user:password@localhost:5432/land_liquidity"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        calculator = FeatureCalculator(session)
        
        # Рассчитываем признаки для участка с ID 1
        result = calculator.calculate_all_features(1)
        
        print(f"Расчет признаков для участка {result.parcel_id}")
        print(f"Время расчета: {result.calculation_time:.2f} секунд")
        print(f"Количество признаков: {len(result.features)}")
        print(f"Ошибки: {result.errors}")
        
        # Сохраняем признаки в базу данных
        if result.features:
            success = calculator.save_features_to_database(
                result.parcel_id, result.features
            )
            print(f"Сохранение в БД: {'Успешно' if success else 'Ошибка'}")
        
        # Выводим первые 10 признаков
        for i, (name, value) in enumerate(list(result.features.items())[:10]):
            print(f"  {name}: {value}")
            
    except Exception as e:
        logger.error(f"Ошибка в примере использования: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()