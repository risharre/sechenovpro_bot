"""
Подключение к базе данных Supabase
"""

import asyncio
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from ..bot.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """Класс для работы с подключением к Supabase"""
    
    _instance: Optional["DatabaseConnection"] = None
    _client: Optional[Client] = None
    
    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = self._create_client()
    
    def _create_client(self) -> Client:
        """Создание клиента Supabase"""
        try:
            client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            logger.info("✅ Подключение к Supabase установлено")
            return client
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Supabase: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Получение клиента Supabase"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    async def test_connection(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            # Простой запрос для проверки соединения
            result = self.client.table("participants").select("count", count="exact").execute()
            logger.info("✅ Подключение к базе данных работает")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка проверки подключения: {e}")
            return False
    
    async def init_database(self) -> bool:
        """Инициализация схемы базы данных"""
        try:
            # Проверяем существование таблиц
            await self.test_connection()
            logger.info("✅ База данных инициализирована")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            return False


# Глобальный экземпляр подключения
db = DatabaseConnection()


def get_database() -> DatabaseConnection:
    """Получение экземпляра подключения к БД"""
    return db 