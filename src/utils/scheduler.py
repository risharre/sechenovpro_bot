"""
Планировщик автоматических рассылок с учетом переходов между станциями
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Callable, Any
from ..bot.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EventScheduler:
    """Планировщик мероприятия с учетом времени переходов"""
    
    def __init__(self):
        self.event_start_time: Optional[datetime] = None
        self.is_running: bool = False
        self.current_station: int = 0
        self.tasks: Dict[str, asyncio.Task] = {}
        self.callbacks: Dict[str, Callable] = {}
    
    def register_callback(self, event_type: str, callback: Callable):
        """Регистрация callback функций для событий"""
        self.callbacks[event_type] = callback
        logger.info(f"Зарегистрирован callback для события: {event_type}")
    
    async def start_event(self, start_time: Optional[datetime] = None) -> bool:
        """Запуск мероприятия"""
        if self.is_running:
            logger.warning("Мероприятие уже запущено")
            return False
        
        self.event_start_time = start_time or datetime.now()
        self.is_running = True
        self.current_station = 0
        
        logger.info(f"🚀 Мероприятие запущено в {self.event_start_time.strftime('%H:%M:%S')}")
        
        # Уведомляем о старте
        if "event_started" in self.callbacks:
            await self.callbacks["event_started"](self.event_start_time)
        
        # Планируем все станции
        await self._schedule_all_stations()
        
        return True
    
    async def stop_event(self) -> bool:
        """Остановка мероприятия"""
        if not self.is_running:
            logger.warning("Мероприятие не запущено")
            return False
        
        self.is_running = False
        
        # Отменяем все задачи
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                logger.info(f"Отменена задача: {task_name}")
        
        self.tasks.clear()
        
        # Уведомляем об остановке
        if "event_stopped" in self.callbacks:
            await self.callbacks["event_stopped"]()
        
        logger.info("🛑 Мероприятие остановлено")
        return True
    
    async def _schedule_all_stations(self):
        """Планирование всех станций с учетом переходов"""
        if not self.event_start_time:
            return
        
        current_time = self.event_start_time
        
        for station_num in range(1, Config.TOTAL_STATIONS + 1):
            # Планируем начало работы на станции
            station_start_task = asyncio.create_task(
                self._schedule_station_start(station_num, current_time)
            )
            self.tasks[f"station_{station_num}_start"] = station_start_task
            
            # Время работы на станции
            work_end_time = current_time + timedelta(minutes=Config.STATION_DURATION_MINUTES)
            
            # Планируем уведомление о переходе (кроме последней станции)
            if station_num < Config.TOTAL_STATIONS:
                transition_task = asyncio.create_task(
                    self._schedule_transition_notification(station_num, work_end_time)
                )
                self.tasks[f"station_{station_num}_transition"] = transition_task
                
                # Время перехода к следующей станции
                current_time = work_end_time + timedelta(minutes=Config.TRANSITION_DURATION_MINUTES)
            else:
                # Планируем завершение мероприятия
                completion_task = asyncio.create_task(
                    self._schedule_event_completion(work_end_time)
                )
                self.tasks["event_completion"] = completion_task
        
        logger.info(f"Запланировано {len(self.tasks)} задач для {Config.TOTAL_STATIONS} станций")
    
    async def _schedule_station_start(self, station_num: int, start_time: datetime):
        """Планирование начала работы на станции"""
        delay = (start_time - datetime.now()).total_seconds()
        
        if delay > 0:
            await asyncio.sleep(delay)
        
        if not self.is_running:
            return
        
        self.current_station = station_num
        logger.info(f"🏁 Начало станции {station_num}")
        
        # Уведомляем о новой станции
        if "station_started" in self.callbacks:
            await self.callbacks["station_started"](station_num)
    
    async def _schedule_transition_notification(self, station_num: int, transition_time: datetime):
        """Планирование уведомления о переходе"""
        delay = (transition_time - datetime.now()).total_seconds()
        
        if delay > 0:
            await asyncio.sleep(delay)
        
        if not self.is_running:
            return
        
        logger.info(f"🚶‍♂️ Переход после станции {station_num}")
        
        # Уведомляем о переходе
        if "transition_started" in self.callbacks:
            await self.callbacks["transition_started"](station_num, station_num + 1)
    
    async def _schedule_event_completion(self, completion_time: datetime):
        """Планирование завершения мероприятия"""
        delay = (completion_time - datetime.now()).total_seconds()
        
        if delay > 0:
            await asyncio.sleep(delay)
        
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("🎊 Мероприятие завершено")
        
        # Уведомляем о завершении
        if "event_completed" in self.callbacks:
            await self.callbacks["event_completed"]()
    
    def get_current_status(self) -> Dict[str, Any]:
        """Получение текущего статуса мероприятия"""
        if not self.is_running or not self.event_start_time:
            return {
                "is_running": False,
                "current_station": 0,
                "elapsed_minutes": 0,
                "remaining_minutes": 0
            }
        
        now = datetime.now()
        elapsed = (now - self.event_start_time).total_seconds() / 60
        total_duration = Config().TOTAL_EVENT_DURATION_MINUTES
        remaining = max(0, total_duration - elapsed)
        
        return {
            "is_running": self.is_running,
            "current_station": self.current_station,
            "elapsed_minutes": int(elapsed),
            "remaining_minutes": int(remaining),
            "start_time": self.event_start_time.strftime("%H:%M:%S"),
            "progress_percentage": min(100, (elapsed / total_duration) * 100)
        }
    
    def get_station_timing(self, station_num: int) -> Dict[str, str]:
        """Получение времени конкретной станции"""
        if not self.event_start_time:
            return {}
        
        # Рассчитываем время начала станции
        minutes_offset = (station_num - 1) * Config.TOTAL_CYCLE_MINUTES
        station_start = self.event_start_time + timedelta(minutes=minutes_offset)
        station_end = station_start + timedelta(minutes=Config.STATION_DURATION_MINUTES)
        
        timing = {
            "start_time": station_start.strftime("%H:%M"),
            "end_time": station_end.strftime("%H:%M"),
            "duration": f"{Config.STATION_DURATION_MINUTES} мин"
        }
        
        # Добавляем время перехода (кроме последней станции)
        if station_num < Config.TOTAL_STATIONS:
            transition_end = station_end + timedelta(minutes=Config.TRANSITION_DURATION_MINUTES)
            timing["transition_end"] = transition_end.strftime("%H:%M")
            timing["transition_duration"] = f"{Config.TRANSITION_DURATION_MINUTES} мин"
        
        return timing


# Глобальный экземпляр планировщика
event_scheduler = EventScheduler()


def get_event_scheduler() -> EventScheduler:
    """Получение экземпляра планировщика"""
    return event_scheduler 