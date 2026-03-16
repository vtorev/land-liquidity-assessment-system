"""Тесты для Telegram бота"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from bot import LandLiquidityBot
from handlers.start_handler import start
from services.api_client import APIClient


class TestBot:
    """Тесты основного бота"""
    
    @pytest.fixture
    def bot(self):
        """Фикстура бота"""
        return LandLiquidityBot()
    
    @pytest.fixture
    def mock_update(self):
        """Фикстура mock update"""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 123456
        update.effective_user.first_name = "Test"
        update.effective_user.last_name = "User"
        update.effective_user.username = "testuser"
        update.effective_message = Mock(spec=Message)
        update.effective_message.text = "test message"
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = 123456
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Фикстура mock context"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.bot = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self, bot):
        """Тест инициализации бота"""
        assert bot.app is not None
        assert bot.config is not None
        assert bot.notification_service is None
    
    @pytest.mark.asyncio
    async def test_start_handler(self, mock_update, mock_context):
        """Тест обработчика команды /start"""
        await start(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        args = mock_update.message.reply_text.call_args
        assert "Добро пожаловать" in args[0][0]


class TestAPIClient:
    """Тесты API клиента"""
    
    @pytest.mark.asyncio
    async def test_search_parcel_success(self):
        """Тест успешного поиска участка"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'cadastral_number': '78:12:0000101:123',
                'address': 'г. Москва, ул. Тестовая, д. 1',
                'area': 1000.0,
                'category': 'ИЖС',
                'purpose': 'Индивидуальное жилищное строительство'
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with APIClient() as client:
                result = await client.search_parcel('78:12:0000101:123')
                
                assert result is not None
                assert result.cadastral_number == '78:12:0000101:123'
                assert result.address == 'г. Москва, ул. Тестовая, д. 1'
    
    @pytest.mark.asyncio
    async def test_search_parcel_not_found(self):
        """Тест поиска несуществующего участка"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with APIClient() as client:
                result = await client.search_parcel('invalid_number')
                
                assert result is None
    
    @pytest.mark.asyncio
    async def test_evaluate_liquidity_success(self):
        """Тест успешной оценки ликвидности"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'cadastral_number': '78:12:0000101:123',
                'liquidity_score': 0.75,
                'liquidity_category': 'high',
                'predicted_price': 5000000.0
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            evaluation_data = {
                'cadastral_number': '78:12:0000101:123',
                'area': 1000.0,
                'category': 'ИЖС'
            }
            
            async with APIClient() as client:
                result = await client.evaluate_liquidity(evaluation_data)
                
                assert result is not None
                assert result.liquidity_score == 0.75
                assert result.liquidity_category == 'high'


class TestValidators:
    """Тесты валидаторов"""
    
    def test_validate_cadastral_number_valid(self):
        """Тест валидации правильного кадастрового номера"""
        from utils.validators import validate_cadastral_number
        
        valid_numbers = [
            '78:12:0000101:123',
            '77:01:0000101:001',
            '50:25:0123456:789'
        ]
        
        for number in valid_numbers:
            assert validate_cadastral_number(number) == True
    
    def test_validate_cadastral_number_invalid(self):
        """Тест валидации неправильного кадастрового номера"""
        from utils.validators import validate_cadastral_number
        
        invalid_numbers = [
            '78-12-0000101-123',
            '78:12:101:123',
            '78:12:0000101:12345',
            'invalid_number',
            ''
        ]
        
        for number in invalid_numbers:
            assert validate_cadastral_number(number) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])