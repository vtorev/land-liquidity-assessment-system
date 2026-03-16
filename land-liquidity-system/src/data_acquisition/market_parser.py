"""
Парсеры для сбора рыночных данных с различных платформ
"""

import requests
import json
import logging
import time
from typing import List, Dict, Optional, Generator
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urlencode
import re
from bs4 import BeautifulSoup

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MarketListing:
    """Модель рыночного объявления"""
    title: str
    price: Optional[float]
    price_per_unit: Optional[float]
    area: Optional[float]
    cadastral_number: Optional[str]
    address: Optional[str]
    description: Optional[str]
    listing_url: str
    source: str
    source_id: str
    listing_date: Optional[datetime]
    status: str = "active"


class AvitoParser:
    """Парсер для Avito"""
    
    def __init__(self):
        self.base_url = "https://www.avito.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Ограничение скорости запросов
        self.rate_limit_delay = 2.0  # секунды между запросами
    
    def search_land_listings(self, region: str = "sankt-peterburg", 
                           radius: int = 50, limit: int = 100) -> List[MarketListing]:
        """
        Поиск объявлений о продаже земли
        
        Args:
            region: Регион поиска
            radius: Радиус поиска в км
            limit: Максимальное количество объявлений
            
        Returns:
            Список объявлений
        """
        listings = []
        page = 1
        
        while len(listings) < limit:
            try:
                # Формирование URL для поиска
                search_params = {
                    'q': 'земля ижс',
                    'radius': radius,
                    'p': page,
                    'user': 1,  # Частные объявления
                }
                
                url = f"{self.base_url}/{region}/zemlya_i_uchastki/prodam?{urlencode(search_params)}"
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Парсинг HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('div', class_='iva-item-content')
                
                if not items:
                    logger.info(f"Объявления на странице {page} не найдены")
                    break
                
                for item in items:
                    if len(listings) >= limit:
                        break
                    
                    listing = self._parse_avito_item(item)
                    if listing:
                        listings.append(listing)
                
                logger.info(f"Обработано страницу {page}, найдено {len(listings)} объявлений")
                page += 1
                
                # Пауза между запросами
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Ошибка при парсинге Avito: {e}")
                break
        
        return listings
    
    def _parse_avito_item(self, item) -> Optional[MarketListing]:
        """Парсинг одного объявления Avito"""
        try:
            # Название
            title_elem = item.find('h3', class_='title-root')
            title = title_elem.get_text(strip=True) if title_elem else "Неизвестно"
            
            # Цена
            price_elem = item.find('span', class_='price-text')
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d\s]+', price_text)
                if price_match:
                    price = float(price_match.group().replace(' ', ''))
            
            # Ссылка
            link_elem = item.find('a', class_='link-root')
            listing_url = self.base_url + link_elem['href'] if link_elem else ""
            
            # ID объявления
            source_id = link_elem['href'].split('/')[-1] if link_elem else ""
            
            # Описание
            description_elem = item.find('div', class_='text-text')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Адрес
            address_elem = item.find('div', class_='address-root')
            address = address_elem.get_text(strip=True) if address_elem else ""
            
            return MarketListing(
                title=title,
                price=price,
                price_per_unit=None,  # Нужно дополнительно рассчитывать
                area=None,  # Нужно извлекать из описания
                cadastral_number=None,
                address=address,
                description=description,
                listing_url=listing_url,
                source="avito",
                source_id=source_id,
                listing_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге элемента Avito: {e}")
            return None


class CianParser:
    """Парсер для Циан"""
    
    def __init__(self):
        self.base_url = "https://api.cian.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Referer': 'https://www.cian.ru/',
        })
        
        self.rate_limit_delay = 1.5
    
    def search_land_listings(self, region_id: int = 2, limit: int = 100) -> List[MarketListing]:
        """
        Поиск объявлений на Циан
        
        Args:
            region_id: ID региона (2 - Санкт-Петербург)
            limit: Максимальное количество объявлений
            
        Returns:
            Список объявлений
        """
        listings = []
        
        try:
            # Циан использует GraphQL API
            query = {
                "operationName": "SearchEngineV3",
                "variables": {
                    "engine_version": "4",
                    "region": [region_id],
                    "category": "land",
                    "offerType": "sale",
                    "page": 1,
                    "pageSize": min(limit, 50),
                    "sort": "creation_date_desc"
                },
                "query": """
                query SearchEngineV3($engine_version: String!, $region: [Int!]!, $category: String!, $offerType: String!, $page: Int!, $pageSize: Int!, $sort: String!) {
                  search(engine_version: $engine_version, region: $region, category: $category, offerType: $offerType, page: $page, pageSize: $pageSize, sort: $sort) {
                    results {
                      id
                      title
                      price
                      pricePerMeter
                      area
                      address
                      description
                      url
                      createdAt
                    }
                    total
                  }
                }
                """
            }
            
            response = self.session.post(
                f"{self.base_url}/graphql/search-engine/v3/",
                json=query,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get('data', {}).get('search', {}).get('results', [])
            
            for item in results:
                listings.append(MarketListing(
                    title=item.get('title', ''),
                    price=item.get('price'),
                    price_per_unit=item.get('pricePerMeter'),
                    area=item.get('area'),
                    cadastral_number=None,
                    address=item.get('address'),
                    description=item.get('description'),
                    listing_url=item.get('url', ''),
                    source="cian",
                    source_id=str(item.get('id', '')),
                    listing_date=datetime.fromisoformat(item.get('createdAt', '').replace('Z', '+00:00')) if item.get('createdAt') else None
                ))
            
            logger.info(f"Найдено {len(listings)} объявлений на Циан")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге Циан: {e}")
        
        return listings


class DomofondParser:
    """Парсер для Домофонд"""
    
    def __init__(self):
        self.base_url = "https://api.domofond.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        })
        
        self.rate_limit_delay = 1.0
    
    def search_land_listings(self, city_id: int = 1, limit: int = 100) -> List[MarketListing]:
        """
        Поиск объявлений на Домофонд
        
        Args:
            city_id: ID города (1 - Москва)
            limit: Максимальное количество объявлений
            
        Returns:
            Список объявлений
        """
        listings = []
        
        try:
            params = {
                'cityId': city_id,
                'category': 'land',
                'operationType': 'sale',
                'page': 1,
                'pageSize': min(limit, 100),
                'sort': 'date_desc'
            }
            
            response = self.session.get(
                f"{self.base_url}/api/v1/search",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get('items', [])
            
            for item in results:
                listings.append(MarketListing(
                    title=item.get('title', ''),
                    price=item.get('price'),
                    price_per_unit=item.get('pricePerSquareMeter'),
                    area=item.get('area'),
                    cadastral_number=item.get('cadastralNumber'),
                    address=item.get('address'),
                    description=item.get('description'),
                    listing_url=item.get('url', ''),
                    source="domofond",
                    source_id=str(item.get('id', '')),
                    listing_date=datetime.fromtimestamp(item.get('createdAt', 0)) if item.get('createdAt') else None
                ))
            
            logger.info(f"Найдено {len(listings)} объявлений на Домофонд")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге Домофонд: {e}")
        
        return listings


class MarketDataAggregator:
    """Агрегатор данных с различных платформ"""
    
    def __init__(self):
        self.parsers = {
            'avito': AvitoParser(),
            'cian': CianParser(),
            'domofond': DomofondParser()
        }
    
    def collect_market_data(self, sources: List[str] = None, limit_per_source: int = 50) -> List[MarketListing]:
        """
        Сбор данных с нескольких источников
        
        Args:
            sources: Список источников для парсинга
            limit_per_source: Лимит объявлений с каждого источника
            
        Returns:
            Объединенный список объявлений
        """
        if sources is None:
            sources = ['avito', 'cian', 'domofond']
        
        all_listings = []
        
        for source in sources:
            if source in self.parsers:
                logger.info(f"Сбор данных с {source}")
                try:
                    listings = self.parsers[source].search_land_listings(limit=limit_per_source)
                    all_listings.extend(listings)
                    logger.info(f"С {source} собрано {len(listings)} объявлений")
                except Exception as e:
                    logger.error(f"Ошибка при сборе данных с {source}: {e}")
            else:
                logger.warning(f"Парсер для {source} не найден")
        
        # Удаление дубликатов по URL
        seen_urls = set()
        unique_listings = []
        
        for listing in all_listings:
            if listing.listing_url not in seen_urls:
                seen_urls.add(listing.listing_url)
                unique_listings.append(listing)
        
        logger.info(f"Всего уникальных объявлений: {len(unique_listings)}")
        return unique_listings
    
    def extract_cadastral_numbers(self, text: str) -> List[str]:
        """
        Извлечение кадастровых номеров из текста
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных кадастровых номеров
        """
        # Регулярное выражение для кадастрового номера
        pattern = r'\b\d{2}:\d{2}:\d{7}:\d{1,10}\b'
        matches = re.findall(pattern, text)
        return matches
    
    def normalize_prices(self, listings: List[MarketListing]) -> List[MarketListing]:
        """
        Нормализация цен и расчет цены за сотку
        
        Args:
            listings: Список объявлений
            
        Returns:
            Список объявлений с нормализованными ценами
        """
        normalized_listings = []
        
        for listing in listings:
            # Нормализация цены
            if listing.price and listing.area:
                # Перевод площади в сотки (если в кв.м)
                area_sotki = listing.area
                if listing.area > 1000:  # Если площадь больше 1000, вероятно это в кв.м
                    area_sotki = listing.area / 100
                
                # Расчет цены за сотку
                price_per_sotka = listing.price / area_sotki
                
                listing.price_per_unit = price_per_sotka
            
            normalized_listings.append(listing)
        
        return normalized_listings


def main():
    """Пример использования парсеров"""
    aggregator = MarketDataAggregator()
    
    # Сбор данных с всех источников
    listings = aggregator.collect_market_data(limit_per_source=20)
    
    # Нормализация цен
    listings = aggregator.normalize_prices(listings)
    
    # Вывод первых 5 объявлений
    for i, listing in enumerate(listings[:5]):
        print(f"{i+1}. {listing.title}")
        print(f"   Цена: {listing.price} руб.")
        print(f"   Цена за сотку: {listing.price_per_unit} руб.")
        print(f"   Площадь: {listing.area} соток")
        print(f"   Источник: {listing.source}")
        print(f"   URL: {listing.listing_url}")
        print()
    
    print(f"Всего собрано: {len(listings)} объявлений")


if __name__ == "__main__":
    main()