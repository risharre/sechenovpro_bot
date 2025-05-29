"""
Модуль inline клавиатур для участников и администраторов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


def get_participant_menu() -> InlineKeyboardMarkup:
    """Главное меню участника"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🏁 Текущая станция",
                callback_data="current_station"
            ),
            InlineKeyboardButton(
                text="⏭️ Следующая станция", 
                callback_data="next_station"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Полное расписание",
                callback_data="full_schedule"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Моя информация",
                callback_data="participant_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="📞 Связь с организатором",
                callback_data="contact_organizer"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить меню",
                callback_data="back_to_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📊 Статус мероприятия",
                callback_data="admin_status"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚀 Запустить мероприятие",
                callback_data="admin_start_event"
            ),
            InlineKeyboardButton(
                text="🛑 Остановить мероприятие",
                callback_data="admin_stop_event"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Экспорт участников",
                callback_data="admin_export"
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Объявление",
                callback_data="admin_broadcast"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_station_navigation_menu(current_station: int, total_stations: int = 9) -> InlineKeyboardMarkup:
    """Меню навигации по станциям"""
    keyboard = []
    
    # Строка с номером текущей станции
    station_row = [
        InlineKeyboardButton(
            text=f"📍 Станция {current_station}/{total_stations}",
            callback_data="current_station"
        )
    ]
    keyboard.append(station_row)
    
    # Строка навигации
    nav_row = []
    
    if current_station > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущая",
                callback_data=f"station_{current_station-1}"
            )
        )
    
    if current_station < total_stations:
        nav_row.append(
            InlineKeyboardButton(
                text="➡️ Следующая",
                callback_data=f"station_{current_station+1}"
            )
        )
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Кнопка возврата
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад в меню",
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_menu(action: str, confirm_callback: str, cancel_callback: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Меню подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=confirm_callback
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=cancel_callback
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_event_control_menu(event_active: bool = False) -> InlineKeyboardMarkup:
    """Меню управления мероприятием для админа"""
    keyboard = []
    
    if not event_active:
        # Мероприятие не активно
        keyboard.append([
            InlineKeyboardButton(
                text="🚀 Запустить мероприятие",
                callback_data="confirm_start_event"
            )
        ])
    else:
        # Мероприятие активно
        keyboard.extend([
            [
                InlineKeyboardButton(
                    text="📊 Статус мероприятия",
                    callback_data="admin_status"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛑 Остановить мероприятие",
                    callback_data="confirm_stop_event"
                )
            ]
        ])
    
    # Общие кнопки
    keyboard.extend([
        [
            InlineKeyboardButton(
                text="📋 Список участников", 
                callback_data="admin_participants"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Экспорт отчета",
                callback_data="admin_export"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data="admin_refresh"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_station_details_menu(station_number: int) -> InlineKeyboardMarkup:
    """Детальное меню для конкретной станции"""
    keyboard = []
    
    # Информация о станции
    info_row = [
        InlineKeyboardButton(
            text="📝 Описание станции",
            callback_data=f"station_info_{station_number}"
        )
    ]
    
    if station_number > 1:
        info_row.append(
            InlineKeyboardButton(
                text="📍 Как добраться",
                callback_data=f"station_location_{station_number}"
            )
        )
    
    keyboard.append(info_row)
    
    # Навигация между станциями
    nav_row = []
    
    if station_number > 1:
        nav_row.append(
            InlineKeyboardButton(
                text=f"⬅️ Станция {station_number-1}",
                callback_data=f"goto_station_{station_number-1}"
            )
        )
    
    if station_number < 9:
        nav_row.append(
            InlineKeyboardButton(
                text=f"➡️ Станция {station_number+1}",
                callback_data=f"goto_station_{station_number+1}"
            )
        )
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Полезные действия
    keyboard.append([
        InlineKeyboardButton(
            text="📅 Полное расписание",
            callback_data="full_schedule"
        )
    ])
    
    # Возврат в меню
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_participant_quick_menu() -> InlineKeyboardMarkup:
    """Быстрое меню участника (компактная версия)"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🏁 Моя станция",
                callback_data="current_station"
            ),
            InlineKeyboardButton(
                text="⏭️ Следующая",
                callback_data="next_station"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Расписание",
                callback_data="full_schedule"
            ),
            InlineKeyboardButton(
                text="👤 Мой профиль",
                callback_data="participant_info"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_broadcast_menu() -> InlineKeyboardMarkup:
    """Меню для управления рассылкой"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📢 Создать объявление",
                callback_data="create_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎯 Уведомить о станции",
                callback_data="broadcast_station"
            ),
            InlineKeyboardButton(
                text="🚶‍♂️ Уведомить о переходе",
                callback_data="broadcast_transition"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_export_menu() -> InlineKeyboardMarkup:
    """Меню экспорта данных"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📊 Экспорт всех участников",
                callback_data="export_all_participants"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Статистика по станциям",
                callback_data="export_station_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Отчет о прогрессе",
                callback_data="export_progress_report"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_help_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Меню справки"""
    keyboard = []
    
    if is_admin:
        keyboard.extend([
            [
                InlineKeyboardButton(
                    text="🔧 Команды админа",
                    callback_data="help_admin_commands"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Управление мероприятием",
                    callback_data="help_event_management"
                )
            ]
        ])
    
    keyboard.extend([
        [
            InlineKeyboardButton(
                text="❓ Как участвовать",
                callback_data="help_participation"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ О расписании",
                callback_data="help_schedule"
            )
        ],
        [
            InlineKeyboardButton(
                text="📞 Контакты организаторов",
                callback_data="contact_organizer"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="back_to_menu"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_dynamic_station_menu(current_station: int, has_next: bool = True, has_prev: bool = True) -> InlineKeyboardMarkup:
    """Динамическое меню станции с учетом текущего положения"""
    keyboard = []
    
    # Текущая станция
    keyboard.append([
        InlineKeyboardButton(
            text=f"📍 Станция {current_station} (текущая)",
            callback_data="current_station"
        )
    ])
    
    # Навигация
    nav_buttons = []
    
    if has_prev:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущая",
                callback_data=f"station_{current_station-1}"
            )
        )
    
    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Следующая",
                callback_data=f"station_{current_station+1}"
            )
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Дополнительные опции
    keyboard.extend([
        [
            InlineKeyboardButton(
                text="📋 Все станции",
                callback_data="full_schedule"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_menu"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =================== CALLBACK DATA КОНСТАНТЫ ===================

class CallbackData:
    """Константы для callback_data"""
    
    # Участники
    CURRENT_STATION = "current_station"
    NEXT_STATION = "next_station"
    FULL_SCHEDULE = "full_schedule"
    PARTICIPANT_INFO = "participant_info"
    CONTACT_ORGANIZER = "contact_organizer"
    BACK_TO_MENU = "back_to_menu"
    
    # Админы
    ADMIN_STATUS = "admin_status"
    ADMIN_START_EVENT = "admin_start_event"
    ADMIN_STOP_EVENT = "admin_stop_event"
    ADMIN_EXPORT = "admin_export"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_PARTICIPANTS = "admin_participants"
    ADMIN_REFRESH = "admin_refresh"
    
    # Подтверждения
    CONFIRM_START_EVENT = "confirm_start_event"
    CONFIRM_STOP_EVENT = "confirm_stop_event"
    
    # Экспорт
    EXPORT_ALL_PARTICIPANTS = "export_all_participants"
    EXPORT_STATION_STATS = "export_station_stats"
    EXPORT_PROGRESS_REPORT = "export_progress_report"
    
    # Рассылка
    CREATE_BROADCAST = "create_broadcast"
    BROADCAST_STATION = "broadcast_station"
    BROADCAST_TRANSITION = "broadcast_transition"
    
    # Справка
    HELP_ADMIN_COMMANDS = "help_admin_commands"
    HELP_EVENT_MANAGEMENT = "help_event_management"
    HELP_PARTICIPATION = "help_participation"
    HELP_SCHEDULE = "help_schedule"


def build_station_callback(station_number: int) -> str:
    """Построение callback для конкретной станции"""
    return f"station_{station_number}"


def build_goto_station_callback(station_number: int) -> str:
    """Построение callback для перехода к станции"""
    return f"goto_station_{station_number}"


def parse_station_callback(callback_data: str) -> Optional[int]:
    """Парсинг номера станции из callback_data"""
    try:
        if callback_data.startswith("station_"):
            return int(callback_data.replace("station_", ""))
        elif callback_data.startswith("goto_station_"):
            return int(callback_data.replace("goto_station_", ""))
        return None
    except (ValueError, AttributeError):
        return None


# =================== МЕНЮ ДЛЯ СПЕЦИАЛЬНЫХ СЛУЧАЕВ ===================

def get_maintenance_menu() -> InlineKeyboardMarkup:
    """Меню на время технических работ"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔄 Проверить статус",
                callback_data="check_maintenance_status"
            )
        ],
        [
            InlineKeyboardButton(
                text="📞 Связаться с поддержкой",
                callback_data="contact_organizer"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_error_menu() -> InlineKeyboardMarkup:
    """Меню при ошибке"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔄 Попробовать снова",
                callback_data="retry_action"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📞 Сообщить об ошибке",
                callback_data="report_error"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 