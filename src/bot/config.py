"""
Конфигурация бота и переменные окружения
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Центральная конфигурация приложения"""
    
    # Telegram Bot настройки
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Supabase настройки
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Администраторы (по username в Telegram)
    ADMIN_USERNAMES: List[str] = [
        username.strip().replace("@", "").lower() 
        for username in os.getenv("ADMIN_USERNAMES", "").split(",") 
        if username.strip()
    ]
    
    # Настройки формы CV
    CV_FORM_URL: str = os.getenv("CV_FORM_URL", "https://forms.yandex.ru/cloud/67d6fd5090fa7be3dc213e5f/")
    
    # Технические настройки
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8000"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "30"))
    RETRY_ATTEMPTS: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    
    # 🔄 Обновленные настройки мероприятия (с учетом переходов)
    STATION_DURATION_MINUTES: int = 6  # Время работы на станции
    TRANSITION_DURATION_MINUTES: int = 2  # Время на переход между станциями
    TOTAL_CYCLE_MINUTES: int = 8  # Полный цикл: 6 мин работа + 2 мин переход
    TOTAL_STATIONS: int = 9
    MAX_PARTICIPANTS: int = 150
    
    # Расчетные значения
    @property
    def TOTAL_EVENT_DURATION_MINUTES(self) -> int:
        """Общая продолжительность мероприятия"""
        return (self.TOTAL_STATIONS * self.STATION_DURATION_MINUTES + 
                (self.TOTAL_STATIONS - 1) * self.TRANSITION_DURATION_MINUTES)  # 70 минут
    
    # Пути к файлам
    ROUTES_CSV_PATH: str = "data/routes.csv"
    STATIONS_CONFIG_PATH: str = "stations_config.json"
    
    @classmethod
    def validate(cls) -> None:
        """Валидация обязательных настроек"""
        required_fields = [
            ("BOT_TOKEN", cls.BOT_TOKEN),
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY),
        ]
        
        missing_fields = [
            field_name for field_name, field_value in required_fields 
            if not field_value
        ]
        
        if missing_fields:
            raise ValueError(
                f"Отсутствуют обязательные переменные окружения: {', '.join(missing_fields)}"
            )
        
        if not cls.ADMIN_USERNAMES:
            raise ValueError("Необходимо указать хотя бы одного администратора в ADMIN_USERNAMES")
    
    @classmethod
    def is_admin(cls, telegram_username: Optional[str]) -> bool:
        """Проверка, является ли пользователь администратором по username"""
        if not telegram_username:
            return False
        
        # Убираем @ если есть и приводим к нижнему регистру
        clean_username = telegram_username.replace("@", "").lower()
        return clean_username in cls.ADMIN_USERNAMES


# Проверяем конфигурацию при импорте
try:
    Config.validate()
except ValueError as e:
    print(f"❌ Ошибка конфигурации: {e}")
    exit(1) 