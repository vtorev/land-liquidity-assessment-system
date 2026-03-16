"""
Парсер данных Росреестра для получения информации о кадастровых участках
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from shapely.geometry import shape, Polygon
import geopandas as gpd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import time
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CadastreParcel:
    """Модель кадастрового участка"""
    cadastral_number: str
    area: Optional[float]
    area_unit: Optional[str]
    status: Optional[str]
    category: Optional[str]
    permitted_use: Optional[str]
    address: Optional[str]
    coordinates: Optional[Polygon]
    cadastral_block: Optional[str]
    source: str = "rosreestr"
    source_id: Optional[str] = None


class RosreestrParser:
    """Парсер данных с публичной кадастровой карты Росреестра"""
    
    def __init__(self, base_url: str = "https://pkk.rosreestr.ru/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        })
        
        # Ограничение скорости запросов
        self.rate_limit_delay = 1.0  # секунды между запросами
        
    def get_parcel_by_cadastral_number(self, cadastral_number: str) -> Optional[CadastreParcel]:
        """
        Получение информации об участке по кадастровому номеру
        
        Args:
            cadastral_number: Кадастровый номер в формате "XX:XX:XXXXXXX:XXX"
            
        Returns:
            Объект CadastreParcel или None при ошибке
        """
        try:
            # Формируем URL для запроса
            url = f"{self.base_url}/features/5"
            
            params = {
                'text': cadastral_number,
                'limit': 1,
                'tolerance': 0,
                'token': ''  # Токен может потребоваться в будущем
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('features'):
                logger.warning(f"Участок с кадастровым номером {cadastral_number} не найден")
                return None
                
            feature = data['features'][0]
            properties = feature.get('properties', {})
            geometry = feature.get('geometry')
            
            # Извлечение координат
            coordinates = None
            if geometry and geometry.get('type') == 'Polygon':
                try:
                    coordinates = shape(geometry)
                except Exception as e:
                    logger.error(f"Ошибка обработки геометрии для {cadastral_number}: {e}")
            
            # Извлечение атрибутов
            parcel = CadastreParcel(
                cadastral_number=cadastral_number,
                area=properties.get('area'),
                area_unit=properties.get('area_unit'),
                status=properties.get('status'),
                category=properties.get('category'),
                permitted_use=properties.get('permitted_use'),
                address=properties.get('address'),
                coordinates=coordinates,
                cadastral_block=properties.get('cadastral_block'),
                source_id=str(properties.get('id', ''))
            )
            
            logger.info(f"Успешно получены данные для {cadastral_number}")
            return parcel
            
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса к Росреестру для {cadastral_number}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON для {cadastral_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке {cadastral_number}: {e}")
            return None
        finally:
            # Соблюдаем лимит запросов
            time.sleep(self.rate_limit_delay)
    
    def get_parcel_by_coordinates(self, lat: float, lon: float) -> Optional[CadastreParcel]:
        """
        Получение информации об участке по координатам
        
        Args:
            lat: Широта
            lon: Долгота
            
        Returns:
            Объект CadastreParcel или None при ошибке
        """
        try:
            url = f"{self.base_url}/features/5"
            
            # Запрос по точке с небольшой погрешностью
            params = {
                'sq': f"{lon},{lat}",
                'sqe': 0.0001,  # Погрешность в градусах (~10 метров)
                'limit': 1,
                'token': ''
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('features'):
                logger.warning(f"Участок по координатам {lat}, {lon} не найден")
                return None
                
            feature = data['features'][0]
            properties = feature.get('properties', {})
            geometry = feature.get('geometry')
            
            coordinates = None
            if geometry and geometry.get('type') == 'Polygon':
                try:
                    coordinates = shape(geometry)
                except Exception as e:
                    logger.error(f"Ошибка обработки геометрии по координатам {lat}, {lon}: {e}")
            
            # Извлечение кадастрового номера
            cadastral_number = properties.get('cn') or properties.get('cadastral_number')
            if not cadastral_number:
                logger.warning(f"Кадастровый номер не найден для координат {lat}, {lon}")
                return None
            
            parcel = CadastreParcel(
                cadastral_number=cadastral_number,
                area=properties.get('area'),
                area_unit=properties.get('area_unit'),
                status=properties.get('status'),
                category=properties.get('category'),
                permitted_use=properties.get('permitted_use'),
                address=properties.get('address'),
                coordinates=coordinates,
                cadastral_block=properties.get('cadastral_block'),
                source_id=str(properties.get('id', ''))
            )
            
            logger.info(f"Успешно получены данные для координат {lat}, {lon}")
            return parcel
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных по координатам {lat}, {lon}: {e}")
            return None
        finally:
            time.sleep(self.rate_limit_delay)
    
    def batch_get_parcels(self, cadastral_numbers: List[str]) -> List[CadastreParcel]:
        """
        Пакетное получение данных по списку кадастровых номеров
        
        Args:
            cadastral_numbers: Список кадастровых номеров
            
        Returns:
            Список найденных участков
        """
        results = []
        
        for i, cadastral_number in enumerate(cadastral_numbers):
            logger.info(f"Обработка {i+1}/{len(cadastral_numbers)}: {cadastral_number}")
            
            parcel = self.get_parcel_by_cadastral_number(cadastral_number)
            if parcel:
                results.append(parcel)
            
            # Дополнительная пауза для пакетной обработки
            if (i + 1) % 10 == 0:
                time.sleep(5)  # Длинная пауза после каждых 10 запросов
        
        return results


class CadastreDatabaseManager:
    """Менеджер базы данных для хранения кадастровых данных"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        
    def save_parcel(self, parcel: CadastreParcel, session: Session) -> bool:
        """
        Сохранение участка в базу данных
        
        Args:
            parcel: Объект CadastreParcel
            session: Сессия SQLAlchemy
            
        Returns:
            Успешность сохранения
        """
        try:
            # Проверка существования участка
            existing = session.query(CadastreParcelModel).filter(
                CadastreParcelModel.cadastral_number == parcel.cadastral_number
            ).first()
            
            if existing:
                # Обновление существующей записи
                existing.area = parcel.area
                existing.area_unit = parcel.area_unit
                existing.status = parcel.status
                existing.category = parcel.category
                existing.permitted_use = parcel.permitted_use
                existing.address = parcel.address
                existing.cadastral_block = parcel.cadastral_block
                existing.source = parcel.source
                existing.source_id = parcel.source_id
                existing.updated_at = datetime.utcnow()
                
                if parcel.coordinates:
                    # Преобразуем Shapely Polygon в WKT для PostGIS
                    existing.coordinates = parcel.coordinates.wkt
                
                logger.info(f"Обновлены данные для {parcel.cadastral_number}")
            else:
                # Создание новой записи
                from models import CadastreParcelModel  # Импорт модели
                
                db_parcel = CadastreParcelModel(
                    cadastral_number=parcel.cadastral_number,
                    area=parcel.area,
                    area_unit=parcel.area_unit,
                    status=parcel.status,
                    category=parcel.category,
                    permitted_use=parcel.permitted_use,
                    address=parcel.address,
                    cadastral_block=parcel.cadastral_block,
                    source=parcel.source,
                    source_id=parcel.source_id,
                    coordinates=parcel.coordinates.wkt if parcel.coordinates else None
                )
                
                session.add(db_parcel)
                logger.info(f"Создана новая запись для {parcel.cadastral_number}")
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения участка {parcel.cadastral_number}: {e}")
            return False
    
    def save_batch(self, parcels: List[CadastreParcel]) -> int:
        """
        Пакетное сохранение участков
        
        Args:
            parcels: Список участков для сохранения
            
        Returns:
            Количество успешно сохраненных записей
        """
        from models import CadastreParcelModel
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        success_count = 0
        
        try:
            for parcel in parcels:
                if self.save_parcel(parcel, session):
                    success_count += 1
                    
        finally:
            session.close()
            
        return success_count


def main():
    """Пример использования парсера"""
    parser = RosreestrParser()
    
    # Пример 1: Получение участка по кадастровому номеру
    cadastral_number = "78:12:0000101:123"
    parcel = parser.get_parcel_by_cadastral_number(cadastral_number)
    
    if parcel:
        print(f"Найден участок: {parcel.cadastral_number}")
        print(f"Площадь: {parcel.area} {parcel.area_unit}")
        print(f"Категория: {parcel.category}")
        print(f"Вид использования: {parcel.permitted_use}")
        if parcel.coordinates:
            print(f"Границы: {parcel.coordinates}")
    
    # Пример 2: Получение участка по координатам
    lat, lon = 59.9386, 30.3141  # Координаты Санкт-Петербурга
    parcel = parser.get_parcel_by_coordinates(lat, lon)
    
    if parcel:
        print(f"Найден участок по координатам: {parcel.cadastral_number}")
    
    # Пример 3: Пакетная обработка
    numbers = ["78:12:0000101:123", "78:12:0000101:124"]
    parcels = parser.batch_get_parcels(numbers)
    print(f"Найдено {len(parcels)} участков")


if __name__ == "__main__":
    main()