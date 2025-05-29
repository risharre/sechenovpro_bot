"""
Менеджер текстов и шаблонов сообщений
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..bot.config import Config
from .logger import get_logger

logger = get_logger(__name__)


class TextManager:
    """Менеджер форматирования текстов для бота"""
    
    def __init__(self):
        self.stations_config = self._load_stations_config()
    
    def _load_stations_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации станций"""
        try:
            with open(Config.STATIONS_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации станций: {e}")
            return {}
    
    # =================== СООБЩЕНИЯ УЧАСТНИКАМ ===================
    
    def format_welcome_message(self, participant_number: int) -> str:
        """Сообщение при регистрации участника"""
        event_description = self.stations_config.get("event_description", "")
        
        return f"""🎉 Добро пожаловать на Sechenov Pro Network!

Ваш номер участника: #{participant_number:03d}

📋 ВАЖНО: Заполните форму для создания CV
👤 Укажите информацию о себе в форме, это важно чтобы сформировать демо-версию своего CV

🔗 Форма: {Config.CV_FORM_URL}

После заполнения формы ваш маршрут будет готов!

📝 Инструкция:
• Дождитесь объявления старта
• Бот будет присылать станции каждые 8 минут  
• 6 минут работы + 2 минуты на переход
• Используйте меню для навигации

💡 О мероприятии:
{event_description}

Статус: Ожидание старта мероприятия ⏳"""
    
    def format_already_registered_message(self, participant_number: int, current_station: int) -> str:
        """Сообщение при повторной регистрации"""
        return f"""👋 С возвращением!

Ваш номер участника: #{participant_number:03d}
📊 Текущая станция: {current_station}/9

Используйте меню для навигации по мероприятию."""
    
    def format_event_started_message(self) -> str:
        """Уведомление о старте мероприятия"""
        return f"""🚀 Мероприятие началось!

Первая станция начинается сейчас!
Общее время: 70 минут (9 станций + переходы)

⏰ График:
• 6 минут работы на станции
• 2 минуты на переход

Удачи! 🍀"""
    
    def format_station_message(self, station_number: int, station_letter: str) -> str:
        """Уведомление о новой станции"""
        station_data = self.stations_config.get("stations", {}).get(station_letter, {})
        
        name = station_data.get("name", f"Станция {station_letter}")
        location = station_data.get("location", f"Станция {station_letter}")
        description = station_data.get("description", "Описание станции")
        
        return f"""🏁 Станция {station_number}/9: {name}

📍 Локация: {location}
⏰ Время работы: 6 минут
🚶‍♂️ Переход: 2 минуты после станции

{description}

⬇️ Переходите к станции сейчас!"""
    
    def format_transition_message(self, from_station: int, to_station: int, to_letter: str) -> str:
        """Уведомление о переходе"""
        station_data = self.stations_config.get("stations", {}).get(to_letter, {})
        name = station_data.get("name", f"Станция {to_letter}")
        location = station_data.get("location", f"Станция {to_letter}")
        
        return f"""🚶‍♂️ Время перехода!

Переходите к следующей станции:
🏁 Станция {to_station}/9: {name}

⏰ У вас 2 минуты на переход
📍 Локация: {location}

Следующая станция начнется автоматически!"""
    
    def format_event_completed_message(self) -> str:
        """Сообщение о завершении мероприятия"""
        return f"""🎊 Поздравляем с завершением!

Спасибо за участие в Sechenov Pro Network!
Вы прошли все 9 станций за 70 минут!

🌟 Ваш CV был создан на основе информации из формы
📈 Используйте полученные навыки в карьере!

До встречи на следующих мероприятиях! 👋"""
    
    # =================== МЕНЮ УЧАСТНИКОВ ===================
    
    def format_current_station_info(self, participant_number: int, current_station: int, 
                                  station_letter: str, event_start_time: Optional[datetime] = None) -> str:
        """Информация о текущей станции"""
        if current_station == 0:
            return f"""👤 Участник #{participant_number:03d}
📊 Станция: Ожидание старта
⏰ Статус: Мероприятие не началось

Дождитесь команды /start_event от организатора"""
        
        station_data = self.stations_config.get("stations", {}).get(station_letter, {})
        name = station_data.get("name", f"Станция {station_letter}")
        description = station_data.get("description", "")
        
        time_info = ""
        if event_start_time:
            time_info = self._calculate_station_timing(current_station, event_start_time)
        
        return f"""🏁 Станция {current_station}/9: {name}

📝 Описание:
{description}

{time_info}

👤 Участник #{participant_number:03d}"""
    
    def format_next_station_info(self, current_station: int, next_letter: str) -> str:
        """Информация о следующей станции"""
        if current_station >= 9:
            return "🏁 Вы на финальной станции! Следующей станции нет."
        
        next_station = current_station + 1
        station_data = self.stations_config.get("stations", {}).get(next_letter, {})
        name = station_data.get("name", f"Станция {next_letter}")
        location = station_data.get("location", f"Станция {next_letter}")
        description = station_data.get("description", "")
        
        return f"""⏭️ Следующая станция {next_station}/9: {name}

📍 Локация: {location}

📝 Что вас ждет:
{description}

⏰ Время перехода: 2 минуты
🕒 Время работы: 6 минут"""
    
    def format_full_schedule(self, event_start_time: Optional[datetime] = None) -> str:
        """Полное расписание мероприятия"""
        schedule_text = "📅 Расписание мероприятия\n\n"
        
        if event_start_time:
            schedule_text += f"🚀 Старт: {event_start_time.strftime('%H:%M')}\n\n"
        
        stations = self.stations_config.get("stations", {})
        for i, (letter, station_data) in enumerate(stations.items(), 1):
            name = station_data.get("name", f"Станция {letter}")
            
            if event_start_time:
                # Расчет времени для каждой станции
                start_minutes = (i - 1) * Config.TOTAL_CYCLE_MINUTES
                end_minutes = start_minutes + Config.STATION_DURATION_MINUTES
                
                start_time = event_start_time + timedelta(minutes=start_minutes)
                end_time = event_start_time + timedelta(minutes=end_minutes)
                
                time_str = f" ({start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')})"
                
                if i < 9:  # Не последняя станция
                    transition_end = end_time + timedelta(minutes=Config.TRANSITION_DURATION_MINUTES)
                    time_str += f" + переход до {transition_end.strftime('%H:%M')}"
                else:
                    time_str += " - ФИНИШ"
            else:
                time_str = ""
            
            schedule_text += f"Станция {i}: {name}{time_str}\n"
        
        schedule_text += f"\n⏰ Общая продолжительность: 70 минут"
        return schedule_text
    
    def format_participant_info(self, participant_number: int, current_station: int, 
                              route: str, event_start_time: Optional[datetime] = None) -> str:
        """Информация участника"""
        status = "Работа на станции ✅" if current_station > 0 else "Ожидание старта ⏳"
        
        time_info = ""
        if event_start_time and current_station > 0:
            time_info = self._calculate_participant_timing(current_station, event_start_time)
        
        return f"""👤 Участник #{participant_number:03d}
📊 Станция: {current_station}/9
🗺️ Маршрут: {route}

{time_info}

Статус: {status}"""
    
    def format_contact_organizer(self) -> str:
        """Информация для связи с организатором"""
        return """📞 Связь с организатором

По любым вопросам обращайтесь к организаторам мероприятия:

• Проблемы с регистрацией
• Технические вопросы
• Помощь в навигации

Найдите организатора на мероприятии или напишите в общий чат."""
    
    # =================== АДМИНСКИЕ СООБЩЕНИЯ ===================
    
    def format_admin_status(self, stats: Dict[str, Any], event_start_time: Optional[datetime] = None) -> str:
        """Статус мероприятия для админа"""
        total_participants = stats.get("total_participants", 0)
        current_station = stats.get("current_station", 0)
        event_status = stats.get("event_status", "unknown")
        
        status_emoji = {
            "active": "🟢",
            "completed": "✅", 
            "stopped": "🔴",
            "unknown": "⚪"
        }
        
        status_text = f"""📊 Статус мероприятия

{status_emoji.get(event_status, '⚪')} Статус: {event_status}
👥 Участников: {total_participants}
🏁 Текущая станция: {current_station}/9"""
        
        if event_start_time:
            now = datetime.now()
            elapsed = now - event_start_time
            elapsed_minutes = int(elapsed.total_seconds() / 60)
            remaining_minutes = max(0, 70 - elapsed_minutes)
            
            status_text += f"""
⏰ Прошло времени: {elapsed_minutes} мин
⏳ Осталось времени: {remaining_minutes} мин
📈 Прогресс: {min(100, (elapsed_minutes / 70) * 100):.1f}%"""
        
        # Статистика по станциям
        station_distribution = stats.get("station_distribution", {})
        if station_distribution:
            status_text += "\n\n📍 Распределение по станциям:"
            for station_key, count in station_distribution.items():
                station_num = station_key.replace("station_", "")
                status_text += f"\n• Станция {station_num}: {count} чел."
        
        return status_text
    
    def format_event_start_success(self, participants_count: int) -> str:
        """Уведомление об успешном запуске мероприятия"""
        return f"""✅ Мероприятие успешно запущено!

👥 Уведомлено участников: {participants_count}
⏰ Общая продолжительность: 70 минут
🏁 Количество станций: 9

Автоматическая рассылка активна."""
    
    def format_event_stop_success(self) -> str:
        """Уведомление об остановке мероприятия"""
        return """🛑 Мероприятие остановлено!

Все автоматические уведомления отключены.
Участники будут уведомлены об остановке."""
    
    # =================== УТИЛИТЫ ===================
    
    def _calculate_station_timing(self, station: int, event_start_time: datetime) -> str:
        """Расчет времени для станции"""
        now = datetime.now()
        
        # Время начала текущей станции
        station_start_minutes = (station - 1) * Config.TOTAL_CYCLE_MINUTES
        station_start_time = event_start_time + timedelta(minutes=station_start_minutes)
        
        # Время окончания работы на станции
        work_end_time = station_start_time + timedelta(minutes=Config.STATION_DURATION_MINUTES)
        
        if now < work_end_time:
            # Станция еще идет
            remaining = work_end_time - now
            remaining_minutes = int(remaining.total_seconds() / 60)
            remaining_seconds = int(remaining.total_seconds() % 60)
            return f"⏰ До окончания работы: {remaining_minutes} мин {remaining_seconds} сек"
        else:
            # Время перехода
            if station < 9:
                transition_end_time = work_end_time + timedelta(minutes=Config.TRANSITION_DURATION_MINUTES)
                if now < transition_end_time:
                    remaining = transition_end_time - now
                    remaining_minutes = int(remaining.total_seconds() / 60)
                    remaining_seconds = int(remaining.total_seconds() % 60)
                    return f"🚶‍♂️ Время на переход: {remaining_minutes} мин {remaining_seconds} сек"
                else:
                    return "⏭️ Ожидание следующей станции"
            else:
                return "🎊 Мероприятие завершено!"
    
    def _calculate_participant_timing(self, station: int, event_start_time: datetime) -> str:
        """Расчет времени для участника"""
        return self._calculate_station_timing(station, event_start_time)
    
    def get_station_letter_by_number(self, station_number: int) -> str:
        """Получение буквы станции по номеру"""
        station_mapping = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F", 7: "G", 8: "H", 9: "I"}
        return station_mapping.get(station_number, "A")


# Глобальный экземпляр
_text_manager = None


def get_text_manager() -> TextManager:
    """Получение экземпляра менеджера текстов"""
    global _text_manager
    if _text_manager is None:
        _text_manager = TextManager()
    return _text_manager 