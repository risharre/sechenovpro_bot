"""
Модели данных для Sechenov Pro Bot
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class Participant:
    """Модель участника мероприятия"""
    id: Optional[int] = None
    telegram_id: int = 0
    participant_number: int = 0
    username: Optional[str] = None
    first_name: Optional[str] = None
    registration_time: Optional[datetime] = None
    current_station: int = 0
    route_data: List[str] = None
    is_active: bool = True
    last_activity: Optional[datetime] = None
    
    def __post_init__(self):
        if self.route_data is None:
            self.route_data = []
    
    @property
    def formatted_number(self) -> str:
        """Форматированный номер участника с ведущими нулями"""
        return f"{self.participant_number:03d}"
    
    @property
    def display_name(self) -> str:
        """Имя для отображения"""
        return self.first_name or self.username or f"Участник #{self.formatted_number}"
    
    @property
    def current_station_id(self) -> Optional[str]:
        """ID текущей станции"""
        if self.current_station > 0 and self.current_station <= len(self.route_data):
            return self.route_data[self.current_station - 1]
        return None
    
    @property
    def next_station_id(self) -> Optional[str]:
        """ID следующей станции"""
        if self.current_station < len(self.route_data):
            return self.route_data[self.current_station]
        return None
    
    @property
    def progress_text(self) -> str:
        """Текст прогресса участника"""
        return f"{self.current_station}/{len(self.route_data)}"
    
    @property
    def route_display(self) -> str:
        """Отображение маршрута"""
        return "→".join(self.route_data) if self.route_data else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сохранения в БД"""
        return {
            "telegram_id": self.telegram_id,
            "participant_number": self.participant_number,
            "username": self.username,
            "first_name": self.first_name,
            "current_station": self.current_station,
            "route_data": json.dumps(self.route_data),
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Participant":
        """Создание из словаря (из БД)"""
        route_data = data.get("route_data", "[]")
        if isinstance(route_data, str):
            route_data = json.loads(route_data)
        
        return cls(
            id=data.get("id"),
            telegram_id=data.get("telegram_id", 0),
            participant_number=data.get("participant_number", 0),
            username=data.get("username"),
            first_name=data.get("first_name"),
            registration_time=data.get("registration_time"),
            current_station=data.get("current_station", 0),
            route_data=route_data,
            is_active=data.get("is_active", True),
            last_activity=data.get("last_activity"),
        )


@dataclass
class Event:
    """Модель мероприятия"""
    id: Optional[int] = None
    start_time: Optional[datetime] = None
    is_active: bool = False
    current_station: int = 0
    created_at: Optional[datetime] = None
    
    @property
    def is_running(self) -> bool:
        """Проверка, запущено ли мероприятие"""
        return self.is_active and self.start_time is not None
    
    @property
    def has_finished(self) -> bool:
        """Проверка, завершилось ли мероприятие"""
        from ..bot.config import Config
        return self.current_station >= Config.TOTAL_STATIONS
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сохранения в БД"""
        return {
            "start_time": self.start_time,
            "is_active": self.is_active,
            "current_station": self.current_station,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Создание из словаря (из БД)"""
        return cls(
            id=data.get("id"),
            start_time=data.get("start_time"),
            is_active=data.get("is_active", False),
            current_station=data.get("current_station", 0),
            created_at=data.get("created_at"),
        )


@dataclass
class AdminMessage:
    """Модель сообщения администратору"""
    id: Optional[int] = None
    participant_id: int = 0
    participant_telegram_id: int = 0
    participant_name: str = ""
    message_text: str = ""
    created_at: Optional[datetime] = None
    is_resolved: bool = False
    
    @property
    def formatted_message(self) -> str:
        """Форматированное сообщение для админов"""
        return (
            f"📞 Сообщение от участника:\n\n"
            f"👤 {self.participant_name} (ID: {self.participant_telegram_id})\n"
            f"💬 {self.message_text}\n\n"
            f"⏰ {self.created_at.strftime('%H:%M:%S') if self.created_at else 'Время неизвестно'}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сохранения в БД"""
        return {
            "participant_id": self.participant_id,
            "message_text": self.message_text,
            "is_resolved": self.is_resolved,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdminMessage":
        """Создание из словаря (из БД)"""
        return cls(
            id=data.get("id"),
            participant_id=data.get("participant_id", 0),
            message_text=data.get("message_text", ""),
            created_at=data.get("created_at"),
            is_resolved=data.get("is_resolved", False),
        )


@dataclass
class Station:
    """Модель станции"""
    id: str
    name: str
    location: str
    description: str
    group_info: str
    
    @property
    def formatted_message(self) -> str:
        """Форматированное сообщение о станции"""
        return (
            f"📍 Локация: {self.location}\n"
            f"👥 Ваша группа: {self.group_info}\n\n"
            f"{self.description}\n\n"
            f"⬇️ Переходите к станции сейчас!"
        )
    
    @classmethod
    def from_dict(cls, station_id: str, data: Dict[str, Any]) -> "Station":
        """Создание из конфигурации"""
        return cls(
            id=station_id,
            name=data.get("name", ""),
            location=data.get("location", ""),
            description=data.get("description", ""),
            group_info=data.get("group_info", ""),
        ) 