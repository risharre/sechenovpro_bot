"""
Обработчик CSV файлов с маршрутами участников
"""

import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Set
from ..bot.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RouteManager:
    """Класс для управления маршрутами участников"""
    
    def __init__(self):
        self.routes: Dict[int, List[str]] = {}
        self.stations: Set[str] = set()
        self.loaded = False
    
    def load_routes_from_csv(self, file_path: Optional[str] = None) -> bool:
        """Загрузка маршрутов из CSV файла"""
        if file_path is None:
            file_path = Config.ROUTES_CSV_PATH
        
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"❌ Файл маршрутов не найден: {file_path}")
                return False
            
            # Читаем CSV
            df = pd.read_csv(file_path)
            
            # Проверяем структуру
            required_columns = ["participant_number"] + [f"station_{i}" for i in range(1, Config.TOTAL_STATIONS + 1)]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"❌ Отсутствуют столбцы в CSV: {missing_columns}")
                return False
            
            # Загружаем маршруты
            self.routes = {}
            self.stations = set()
            
            for _, row in df.iterrows():
                participant_number = int(row["participant_number"])
                route = []
                
                for i in range(1, Config.TOTAL_STATIONS + 1):
                    station_id = str(row[f"station_{i}"]).strip().upper()
                    route.append(station_id)
                    self.stations.add(station_id)
                
                self.routes[participant_number] = route
            
            self.loaded = True
            logger.info(f"✅ Загружено маршрутов: {len(self.routes)}, станций: {len(self.stations)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки маршрутов: {e}")
            return False
    
    def validate_routes(self) -> List[str]:
        """Валидация маршрутов"""
        if not self.loaded:
            return ["Маршруты не загружены"]
        
        errors = []
        
        # Проверяем количество участников
        if len(self.routes) > Config.MAX_PARTICIPANTS:
            errors.append(f"Слишком много участников: {len(self.routes)} > {Config.MAX_PARTICIPANTS}")
        
        # Проверяем корректность номеров участников
        expected_numbers = set(range(1, len(self.routes) + 1))
        actual_numbers = set(self.routes.keys())
        
        missing_numbers = expected_numbers - actual_numbers
        if missing_numbers:
            errors.append(f"Отсутствуют номера участников: {sorted(missing_numbers)}")
        
        extra_numbers = actual_numbers - expected_numbers
        if extra_numbers:
            errors.append(f"Лишние номера участников: {sorted(extra_numbers)}")
        
        # Проверяем длину маршрутов
        for participant_number, route in self.routes.items():
            if len(route) != Config.TOTAL_STATIONS:
                errors.append(
                    f"Участник {participant_number}: неверная длина маршрута "
                    f"({len(route)} != {Config.TOTAL_STATIONS})"
                )
        
        # Проверяем уникальность станций в маршрутах
        for participant_number, route in self.routes.items():
            if len(set(route)) != len(route):
                duplicates = [station for station in set(route) if route.count(station) > 1]
                errors.append(f"Участник {participant_number}: дублирующиеся станции {duplicates}")
        
        if not errors:
            logger.info("✅ Валидация маршрутов прошла успешно")
        else:
            logger.warning(f"⚠️ Найдены ошибки в маршрутах: {len(errors)}")
        
        return errors
    
    def get_participant_route(self, participant_number: int) -> Optional[List[str]]:
        """Получение маршрута участника"""
        if not self.loaded:
            logger.warning("Маршруты не загружены")
            return None
        
        return self.routes.get(participant_number)
    
    def get_available_participant_number(self) -> Optional[int]:
        """Получение следующего доступного номера участника"""
        if not self.loaded:
            return None
        
        used_numbers = set(self.routes.keys())
        
        for number in range(1, Config.MAX_PARTICIPANTS + 1):
            if number not in used_numbers:
                return number
        
        return None
    
    def get_all_stations(self) -> Set[str]:
        """Получение всех уникальных станций"""
        return self.stations.copy()
    
    def generate_routes_report(self) -> Dict[str, any]:
        """Генерация отчета по маршрутам"""
        if not self.loaded:
            return {"error": "Маршруты не загружены"}
        
        station_usage = {}
        for station in self.stations:
            station_usage[station] = sum(1 for route in self.routes.values() if station in route)
        
        return {
            "total_participants": len(self.routes),
            "total_stations": len(self.stations),
            "stations": sorted(self.stations),
            "station_usage": station_usage,
            "validation_errors": self.validate_routes()
        }
    
    def export_participant_report(self, participants_data: List[Dict]) -> str:
        """Экспорт отчета участников в CSV"""
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        headers = [
            "Номер участника", "Telegram ID", "Имя", "Username",
            "Текущая станция", "Прогресс", "Маршрут", "Статус", "Время регистрации"
        ]
        writer.writerow(headers)
        
        # Данные участников
        for participant in participants_data:
            route_data = participant.get("route_data", [])
            if isinstance(route_data, str):
                import json
                route_data = json.loads(route_data)
            
            writer.writerow([
                f"{participant.get('participant_number', 0):03d}",
                participant.get("telegram_id", ""),
                participant.get("first_name", ""),
                participant.get("username", ""),
                participant.get("current_station", 0),
                f"{participant.get('current_station', 0)}/{len(route_data)}",
                "→".join(route_data),
                "Активен" if participant.get("is_active", False) else "Неактивен",
                participant.get("registration_time", "")
            ])
        
        return output.getvalue()


# Глобальный экземпляр менеджера маршрутов
route_manager = RouteManager()


def get_route_manager() -> RouteManager:
    """Получение экземпляра менеджера маршрутов"""
    return route_manager 