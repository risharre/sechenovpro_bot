"""
SQL запросы для работы с базой данных Supabase
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from .connection import get_supabase_client
from .models import Participant, Event, AdminMessage
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseQueries:
    """Менеджер SQL запросов для работы с Supabase"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    # =================== УЧАСТНИКИ ===================
    
    async def create_participant(self, telegram_id: int, telegram_username: str, 
                               full_name: str, route: str) -> Optional[Participant]:
        """Создание нового участника"""
        try:
            # Проверяем, не существует ли уже такой участник
            existing = await self.get_participant_by_telegram_id(telegram_id)
            if existing:
                logger.warning(f"Участник с telegram_id {telegram_id} уже существует")
                return existing
            
            # Получаем следующий номер участника
            participant_number = await self._get_next_participant_number()
            
            data = {
                "telegram_id": telegram_id,
                "telegram_username": telegram_username,
                "full_name": full_name,
                "participant_number": participant_number,
                "route": route,
                "current_station": 0,
                "registration_date": datetime.utcnow().isoformat(),
                "is_active": True
            }
            
            response = self.client.table("participants").insert(data).execute()
            
            if response.data:
                logger.info(f"Создан участник #{participant_number}: {full_name}")
                return Participant.from_dict(response.data[0])
            
            logger.error(f"Ошибка создания участника: {response}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания участника: {e}")
            return None
    
    async def get_participant_by_telegram_id(self, telegram_id: int) -> Optional[Participant]:
        """Получение участника по Telegram ID"""
        try:
            response = self.client.table("participants").select("*").eq("telegram_id", telegram_id).execute()
            
            if response.data:
                return Participant.from_dict(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения участника {telegram_id}: {e}")
            return None
    
    async def update_participant_station(self, telegram_id: int, new_station: int) -> bool:
        """Обновление текущей станции участника"""
        try:
            data = {
                "current_station": new_station,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("participants").update(data).eq("telegram_id", telegram_id).execute()
            
            if response.data:
                logger.info(f"Участник {telegram_id} перешел на станцию {new_station}")
                return True
            
            logger.error(f"Ошибка обновления станции участника {telegram_id}")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления станции участника {telegram_id}: {e}")
            return False
    
    async def get_all_active_participants(self) -> List[Participant]:
        """Получение всех активных участников"""
        try:
            response = self.client.table("participants").select("*").eq("is_active", True).execute()
            
            participants = []
            if response.data:
                for participant_data in response.data:
                    participants.append(Participant.from_dict(participant_data))
            
            logger.info(f"Получено {len(participants)} активных участников")
            return participants
            
        except Exception as e:
            logger.error(f"Ошибка получения активных участников: {e}")
            return []
    
    async def get_participants_by_station(self, station: int) -> List[Participant]:
        """Получение участников на определенной станции"""
        try:
            response = self.client.table("participants").select("*").eq("current_station", station).eq("is_active", True).execute()
            
            participants = []
            if response.data:
                for participant_data in response.data:
                    participants.append(Participant.from_dict(participant_data))
            
            return participants
            
        except Exception as e:
            logger.error(f"Ошибка получения участников на станции {station}: {e}")
            return []
    
    async def deactivate_participant(self, telegram_id: int) -> bool:
        """Деактивация участника"""
        try:
            data = {
                "is_active": False,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("participants").update(data).eq("telegram_id", telegram_id).execute()
            
            if response.data:
                logger.info(f"Участник {telegram_id} деактивирован")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка деактивации участника {telegram_id}: {e}")
            return False
    
    async def _get_next_participant_number(self) -> int:
        """Получение следующего номера участника"""
        try:
            response = self.client.table("participants").select("participant_number").order("participant_number", desc=True).limit(1).execute()
            
            if response.data:
                return response.data[0]["participant_number"] + 1
            else:
                return 1  # Первый участник
                
        except Exception as e:
            logger.error(f"Ошибка получения номера участника: {e}")
            return 1
    
    # =================== МЕРОПРИЯТИЯ ===================
    
    async def create_event(self, admin_id: int) -> Optional[Event]:
        """Создание нового мероприятия"""
        try:
            # Завершаем предыдущие активные мероприятия
            await self._deactivate_previous_events()
            
            data = {
                "start_time": datetime.utcnow().isoformat(),
                "created_by": admin_id,
                "status": "active",
                "current_station": 1
            }
            
            response = self.client.table("events").insert(data).execute()
            
            if response.data:
                logger.info(f"Создано новое мероприятие админом {admin_id}")
                return Event.from_dict(response.data[0])
            
            logger.error(f"Ошибка создания мероприятия: {response}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания мероприятия: {e}")
            return None
    
    async def get_active_event(self) -> Optional[Event]:
        """Получение активного мероприятия"""
        try:
            response = self.client.table("events").select("*").eq("status", "active").execute()
            
            if response.data:
                return Event.from_dict(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения активного мероприятия: {e}")
            return None
    
    async def update_event_station(self, event_id: int, new_station: int) -> bool:
        """Обновление текущей станции мероприятия"""
        try:
            data = {
                "current_station": new_station,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("events").update(data).eq("id", event_id).execute()
            
            if response.data:
                logger.info(f"Мероприятие {event_id} перешло на станцию {new_station}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления станции мероприятия {event_id}: {e}")
            return False
    
    async def complete_event(self, event_id: int) -> bool:
        """Завершение мероприятия"""
        try:
            data = {
                "status": "completed",
                "end_time": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("events").update(data).eq("id", event_id).execute()
            
            if response.data:
                logger.info(f"Мероприятие {event_id} завершено")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка завершения мероприятия {event_id}: {e}")
            return False
    
    async def stop_event(self, event_id: int) -> bool:
        """Экстренная остановка мероприятия"""
        try:
            data = {
                "status": "stopped",
                "end_time": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("events").update(data).eq("id", event_id).execute()
            
            if response.data:
                logger.info(f"Мероприятие {event_id} остановлено")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка остановки мероприятия {event_id}: {e}")
            return False
    
    async def _deactivate_previous_events(self) -> bool:
        """Деактивация предыдущих мероприятий"""
        try:
            data = {
                "status": "completed",
                "end_time": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("events").update(data).eq("status", "active").execute()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка деактивации предыдущих мероприятий: {e}")
            return False
    
    # =================== СООБЩЕНИЯ АДМИНАМ ===================
    
    async def create_admin_message(self, telegram_id: int, message_type: str, 
                                 content: str, event_id: Optional[int] = None) -> Optional[AdminMessage]:
        """Создание сообщения админу"""
        try:
            data = {
                "telegram_id": telegram_id,
                "message_type": message_type,
                "content": content,
                "event_id": event_id,
                "created_at": datetime.utcnow().isoformat(),
                "is_read": False
            }
            
            response = self.client.table("admin_messages").insert(data).execute()
            
            if response.data:
                logger.info(f"Создано сообщение админу {telegram_id}: {message_type}")
                return AdminMessage.from_dict(response.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания сообщения админу: {e}")
            return None
    
    async def get_unread_admin_messages(self, telegram_id: int) -> List[AdminMessage]:
        """Получение непрочитанных сообщений админа"""
        try:
            response = self.client.table("admin_messages").select("*").eq("telegram_id", telegram_id).eq("is_read", False).execute()
            
            messages = []
            if response.data:
                for message_data in response.data:
                    messages.append(AdminMessage.from_dict(message_data))
            
            return messages
            
        except Exception as e:
            logger.error(f"Ошибка получения сообщений админа {telegram_id}: {e}")
            return []
    
    async def mark_admin_message_as_read(self, message_id: int) -> bool:
        """Отметка сообщения как прочитанное"""
        try:
            data = {"is_read": True}
            response = self.client.table("admin_messages").update(data).eq("id", message_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Ошибка отметки сообщения {message_id} как прочитанное: {e}")
            return False
    
    # =================== СТАТИСТИКА ===================
    
    async def get_event_statistics(self, event_id: Optional[int] = None) -> Dict[str, Any]:
        """Получение статистики мероприятия"""
        try:
            if not event_id:
                active_event = await self.get_active_event()
                if not active_event:
                    return {}
                event_id = active_event.id
            
            # Общая статистика участников
            participants = await self.get_all_active_participants()
            total_participants = len(participants)
            
            # Статистика по станциям
            station_stats = {}
            for station in range(1, 10):  # 9 станций
                station_participants = await self.get_participants_by_station(station)
                station_stats[f"station_{station}"] = len(station_participants)
            
            # Получение информации о мероприятии
            event = await self.get_active_event()
            
            stats = {
                "event_id": event_id,
                "total_participants": total_participants,
                "current_station": event.current_station if event else 0,
                "station_distribution": station_stats,
                "event_status": event.status if event else "unknown",
                "start_time": event.start_time if event else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики мероприятия: {e}")
            return {}
    
    # =================== ЭКСПОРТ ===================
    
    async def export_participants_csv(self) -> List[Dict[str, Any]]:
        """Экспорт участников в формат CSV"""
        try:
            participants = await self.get_all_active_participants()
            
            csv_data = []
            for participant in participants:
                csv_data.append({
                    "participant_number": participant.participant_number,
                    "telegram_id": participant.telegram_id,
                    "telegram_username": participant.telegram_username,
                    "full_name": participant.full_name,
                    "current_station": participant.current_station,
                    "route": participant.route,
                    "registration_date": participant.registration_date,
                    "last_updated": participant.last_updated,
                    "is_active": participant.is_active
                })
            
            logger.info(f"Экспортировано {len(csv_data)} участников")
            return csv_data
            
        except Exception as e:
            logger.error(f"Ошибка экспорта участников: {e}")
            return []


# Глобальный экземпляр
_db_queries = None


def get_db_queries() -> DatabaseQueries:
    """Получение экземпляра менеджера запросов"""
    global _db_queries
    if _db_queries is None:
        _db_queries = DatabaseQueries()
    return _db_queries 