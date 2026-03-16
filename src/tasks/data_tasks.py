"""
Фоновые задачи для сбора и обработки данных
"""

import logging
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import requests
import json
from datetime import datetime, timedelta
import time

from src.data_acquisition.cadastre_parser import RosreestrParser, CadastreDatabaseManager
from src.models import CadastreParcel, MarketListing, InfrastructureObject
from src.tasks.celery_app import celery_app

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_market_data(self):
    """
    Фоновая задача для обновления рыночных данных
    """
    try:
        logger.info("Начало обновления рыночных данных")
        
        # Здесь будет логика парсинга Avito, Циан и других платформ
        # Пока создадим заглушку
        
        # Пример данных (в реальной системе это будут парситься с сайтов)
        sample_listings = [
            {
                'cadastral_number': '78:12:0000101:123',
                'price': 5000000,
                'price_per_unit': 50000,
                'area': 100,
                'listing_date': datetime.now(),
                'source': 'sample_parser'
            }
        ]
        
        # Сохранение данных в базу
        database_url = "postgresql://postgres:postgres@postgres:5432/land_liquidity"
        manager = CadastreDatabaseManager(database_url)
        
        for listing_data in sample_listings:
            # Поиск участка по кадастровому номеру
            parser = RosreestrParser()
            parcel = parser.get_parcel_by_cadastral_number(listing_data['cadastral_number'])
            
            if parcel:
                # Сохранение рыночной информации
                # В реальной системе это будет отдельная модель MarketListing
                
                logger.info(f"Обновлены рыночные данные для {listing_data['cadastral_number']}")
        
        logger.info("Обновление рыночных данных завершено")
        return {"status": "success", "updated_records": len(sample_listings)}
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении рыночных данных: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def update_infrastructure_data(self):
    """
    Фоновая задача для обновления данных об инфраструктуре
    """
    try:
        logger.info("Начало обновления данных об инфраструктуре")
        
        # Интеграция с OpenStreetMap API
        osm_url = "https://overpass-api.de/api/interpreter"
        
        # Запрос для получения школ в радиусе 50 км от центра города
        overpass_query = """
        [out:json];
        (
          node["amenity"="school"](around:50000,59.9386,30.3141);
          way["amenity"="school"](around:50000,59.9386,30.3141);
          relation["amenity"="school"](around:50000,59.9386,30.3141);
        );
        out center;
        """
        
        response = requests.post(osm_url, data={'data': overpass_query}, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Обработка данных OSM
        schools = []
        for element in data.get('elements', []):
            if element['type'] == 'node':
                lat, lon = element['lat'], element['lon']
            elif element['type'] in ['way', 'relation']:
                lat, lon = element['center']['lat'], element['center']['lon']
            else:
                continue
                
            schools.append({
                'name': element.get('tags', {}).get('name', 'Unknown'),
                'type': 'school',
                'latitude': lat,
                'longitude': lon,
                'source': 'openstreetmap'
            })
        
        logger.info(f"Найдено {len(schools)} школ")
        
        # Сохранение в базу данных
        # В реальной системе здесь будет логика сохранения в InfrastructureObject
        
        logger.info("Обновление данных об инфраструктуре завершено")
        return {"status": "success", "schools_found": len(schools)}
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных об инфраструктуре: {e}")
        raise self.retry(countdown=120, exc=e)


@shared_task(bind=True, max_retries=3)
def update_cadastre_data(self, cadastral_numbers):
    """
    Фоновая задача для обновления кадастровых данных
    
    Args:
        cadastral_numbers: Список кадастровых номеров для обновления
    """
    try:
        logger.info(f"Начало обновления кадастровых данных для {len(cadastral_numbers)} участков")
        
        parser = RosreestrParser()
        manager = CadastreDatabaseManager("postgresql://postgres:postgres@postgres:5432/land_liquidity")
        
        success_count = 0
        error_count = 0
        
        for cadastral_number in cadastral_numbers:
            try:
                parcel = parser.get_parcel_by_cadastral_number(cadastral_number)
                if parcel:
                    # В реальной системе здесь будет сохранение в базу
                    success_count += 1
                    logger.info(f"Успешно обновлен {cadastral_number}")
                else:
                    error_count += 1
                    logger.warning(f"Не удалось найти {cadastral_number}")
                    
                # Пауза между запросами для соблюдения лимитов
                time.sleep(1)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Ошибка при обновлении {cadastral_number}: {e}")
        
        logger.info(f"Обновление кадастровых данных завершено: {success_count} успешных, {error_count} ошибок")
        return {
            "status": "completed",
            "success_count": success_count,
            "error_count": error_count,
            "total": len(cadastral_numbers)
        }
        
    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении кадастровых данных: {e}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def cleanup_old_data(self):
    """
    Фоновая задача для очистки старых данных
    """
    try:
        logger.info("Начало очистки старых данных")
        
        # Удаление данных старше 1 года
        cutoff_date = datetime.now() - timedelta(days=365)
        
        # В реальной системе здесь будет логика удаления старых записей
        # Например: удаление старых логов, временных файлов, устаревших кэшей
        
        logger.info("Очистка старых данных завершена")
        return {"status": "success", "cutoff_date": cutoff_date.isoformat()}
        
    except Exception as e:
        logger.error(f"Ошибка при очистке старых данных: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def process_parcel_features(self, parcel_id):
    """
    Фоновая задача для расчета признаков участка
    
    Args:
        parcel_id: ID участка для расчета признаков
    """
    try:
        logger.info(f"Начало расчета признаков для участка {parcel_id}")
        
        from src.feature_engineering.feature_calculator import FeatureCalculator
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
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
def download_osm_data(self, region_name="russia"):
    """
    Фоновая задача для загрузки OSM данных
    
    Args:
        region_name: Название региона для загрузки
    """
    try:
        logger.info(f"Начало загрузки OSM данных для {region_name}")
        
        # URL для загрузки OSM данных (Geofabrik)
        base_url = "https://download.geofabrik.de"
        file_url = f"{base_url}/russia-latest.osm.pbf"
        
        # Загрузка файла
        response = requests.get(file_url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Сохранение файла
        file_path = f"/data/{region_name}-latest.osm.pbf"
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"OSM данные для {region_name} успешно загружены: {file_path}")
        return {
            "status": "success",
            "file_path": file_path,
            "region": region_name
        }
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке OSM данных: {e}")
        raise self.retry(countdown=600, exc=e)


@shared_task(bind=True, max_retries=3)
def process_satellite_imagery(self, parcel_id, date_range):
    """
    Фоновая задача для обработки спутниковых снимков
    
    Args:
        parcel_id: ID участка
        date_range: Диапазон дат для получения снимков
    """
    try:
        logger.info(f"Начало обработки спутниковых снимков для участка {parcel_id}")
        
        # Интеграция с Sentinel Hub API или другими спутниковыми сервисами
        # Пока создадим заглушку
        
        # Пример обработки спутниковых данных
        satellite_data = {
            'ndvi': 0.65,
            'ndwi': 0.25,
            'ndbi': 0.15,
            'elevation': 150.5,
            'slope': 5.2,
            'aspect': 180.0,
            'date_acquired': datetime.now()
        }
        
        # В реальной системе здесь будет сохранение в SatelliteData
        
        logger.info(f"Обработка спутниковых снимков для участка {parcel_id} завершена")
        return {
            "status": "success",
            "parcel_id": parcel_id,
            "satellite_data": satellite_data
        }
        
    except Exception as e:
        logger.error(f"Ошибка при обработке спутниковых снимков: {e}")
        raise self.retry(countdown=120, exc=e)