"""Сервис для работы с backend API"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ParcelData:
    """Данные участка"""
    cadastral_number: str
    address: str
    area: float
    category: str
    purpose: str
    coordinates: Optional[Dict[str, float]] = None


@dataclass
class EvaluationResult:
    """Результат оценки ликвидности"""
    cadastral_number: str
    liquidity_score: float
    liquidity_category: str
    predicted_price: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None


@dataclass
class AnalyticsData:
    """Данные рыночной аналитики"""
    region: str
    average_price: float
    trend: str
    comparables: List[Dict[str, Any]]


class APIClient:
    """Клиент для взаимодействия с backend API"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """
        Инициализация API клиента
        
        Args:
            base_url: Базовый URL backend API
            timeout: Таймаут запросов в секундах
        """
        config = Config.get_bot_config()
        self.base_url = base_url or config.api_base_url
        self.timeout = timeout or config.api_timeout
        self.session = None
    
    async def __aenter__(self):
        """Контекстный менеджер для создания сессии"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    async def search_parcel(self, cadastral_number: str) -> Optional[ParcelData]:
        """Поиск участка по кадастровому номеру"""
        try:
            url = f"{self.base_url}/parcels/search"
            data = {"cadastral_number": cadastral_number}
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return ParcelData(**result)
                else:
                    logger.warning(f"Ошибка поиска участка: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Ошибка при поиске участка: {e}")
            return None
    
    async def evaluate_liquidity(self, evaluation_data: Dict[str, Any]) -> Optional[EvaluationResult]:
        """Оценка ликвидности участка"""
        try:
            url = f"{self.base_url}/evaluate"
            
            async with self.session.post(url, json=evaluation_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return EvaluationResult(**result)
                else:
                    logger.warning(f"Ошибка оценки ликвидности: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Ошибка при оценке ликвидности: {e}")
            return None
    
    async def get_parcel_analytics(self, cadastral_number: str) -> Optional[AnalyticsData]:
        """Получение рыночной аналитики по участку"""
        try:
            url = f"{self.base_url}/analytics/parcel/{cadastral_number}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return AnalyticsData(**result)
                else:
                    logger.warning(f"Ошибка получения аналитики: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Ошибка при получении аналитики: {e}")
            return None
    
    async def get_market_analytics(self, region: str, limit: int = 10) -> Optional[AnalyticsData]:
        """Получение рыночной аналитики по региону"""
        try:
            url = f"{self.base_url}/analytics/market"
            params = {"region": region, "limit": limit}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return AnalyticsData(**result)
                else:
                    logger.warning(f"Ошибка получения рыночной аналитики: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Ошибка при получении рыночной аналитики: {e}")
            return None
    
    async def get_user_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение уведомлений для пользователя"""
        try:
            url = f"{self.base_url}/notifications/user/{user_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Ошибка получения уведомлений: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Ошибка при получении уведомлений: {e}")
            return []
    
    async def subscribe_to_notifications(self, user_id: int, cadastral_number: str) -> bool:
        """Подписка на уведомления об участке"""
        try:
            url = f"{self.base_url}/notifications/subscribe"
            data = {
                "user_id": user_id,
                "cadastral_number": cadastral_number
            }
            
            async with self.session.post(url, json=data) as response:
                return response.status == 200
        
        except Exception as e:
            logger.error(f"Ошибка при подписке на уведомления: {e}")
            return False
    
    async def unsubscribe_from_notifications(self, user_id: int, cadastral_number: str) -> bool:
        """Отписка от уведомлений об участке"""
        try:
            url = f"{self.base_url}/notifications/unsubscribe"
            data = {
                "user_id": user_id,
                "cadastral_number": cadastral_number
            }
            
            async with self.session.post(url, json=data) as response:
                return response.status == 200
        
        except Exception as e:
            logger.error(f"Ошибка при отписке от уведомлений: {e}")
            return False


# Функции для удобства использования
async def search_parcel(cadastral_number: str) -> Optional[ParcelData]:
    """Удобная функция для поиска участка"""
    async with APIClient() as client:
        return await client.search_parcel(cadastral_number)


async def evaluate_liquidity(evaluation_data: Dict[str, Any]) -> Optional[EvaluationResult]:
    """Удобная функция для оценки ликвидности"""
    async with APIClient() as client:
        return await client.evaluate_liquidity(evaluation_data)


async def get_parcel_analytics(cadastral_number: str) -> Optional[AnalyticsData]:
    """Удобная функция для получения аналитики по участку"""
    async with APIClient() as client:
        return await client.get_parcel_analytics(cadastral_number)


async def get_market_analytics(region: str, limit: int = 10) -> Optional[AnalyticsData]:
    """Удобная функция для получения рыночной аналитики"""
    async with APIClient() as client:
        return await client.get_market_analytics(region, limit)