# Архитектура Sechenov Pro Bot

## 📁 Структура проекта

```
sechenovpro_bot/
├── src/                          # Исходный код
│   ├── bot/                      # Основная логика бота
│   │   ├── __init__.py
│   │   ├── main.py              # Точка входа
│   │   └── config.py            # Конфигурация бота
│   ├── handlers/                 # Обработчики команд и сообщений
│   │   ├── __init__.py
│   │   ├── participant.py       # Команды участников
│   │   ├── admin.py             # Команды администраторов
│   │   └── menu.py              # Inline кнопки меню
│   ├── database/                 # Работа с базой данных
│   │   ├── __init__.py
│   │   ├── models.py            # Модели данных
│   │   ├── connection.py        # Подключение к Supabase
│   │   └── queries.py           # SQL запросы
│   ├── utils/                    # Вспомогательные функции
│   │   ├── __init__.py
│   │   ├── scheduler.py         # Планировщик рассылок
│   │   ├── csv_handler.py       # Работа с CSV файлами
│   │   ├── text_manager.py      # Управление текстами
│   │   └── logger.py            # Логирование
│   └── middleware/               # Промежуточное ПО
│       ├── __init__.py
│       ├── auth.py              # Авторизация админов
│       └── rate_limit.py        # Ограничение частоты запросов
├── tests/                        # Тесты
│   ├── test_handlers.py
│   ├── test_database.py
│   └── test_utils.py
├── data/                         # Файлы данных
│   ├── routes.csv               # Маршруты участников
│   └── stations_config.json     # Конфигурация станций
├── logs/                         # Логи (создается автоматически)
├── requirements.txt              # Зависимости Python
├── env_example.txt              # Пример переменных окружения
├── README.md                     # Основная документация
├── DEPLOYMENT.md                 # Руководство по развертыванию
├── ARCHITECTURE.md              # Этот файл
└── routes_example.csv           # Пример файла маршрутов
```

## 🏗️ Компоненты системы

### 1. Bot Core (`src/bot/`)

**main.py** - Точка входа приложения
- Инициализация бота и диспетчера
- Подключение handlers и middleware
- Запуск polling/webhook

**config.py** - Централизованная конфигурация
- Загрузка переменных окружения
- Валидация настроек
- Константы приложения

### 2. Handlers (`src/handlers/`)

**participant.py** - Обработчики команд участников
```python
# Основные функции:
- handle_start()         # Регистрация участника
- handle_current_station() # Показ текущей станции
- handle_next_station()    # Показ следующей станции
- handle_my_info()         # Информация об участнике
- handle_contact_admin()   # Связь с организатором
```

**admin.py** - Обработчики команд администраторов
```python
# Основные функции:
- handle_start_event()   # Запуск мероприятия
- handle_stop_event()    # Остановка мероприятия
- handle_report()        # Генерация отчетов
- handle_stats()         # Статистика
- handle_broadcast()     # Массовая рассылка
```

**menu.py** - Обработчики inline клавиатуры
```python
# Callback handlers:
- callback_current_station()
- callback_next_station()
- callback_contact_admin()
- callback_my_info()
```

### 3. Database Layer (`src/database/`)

**models.py** - Модели данных
```python
@dataclass
class Participant:
    id: int
    telegram_id: int
    participant_number: int
    username: str
    first_name: str
    current_station: int
    route_data: list
    is_active: bool

@dataclass
class Event:
    id: int
    start_time: datetime
    is_active: bool
    current_station: int

@dataclass
class AdminMessage:
    id: int
    participant_id: int
    message_text: str
    created_at: datetime
    is_resolved: bool
```

**connection.py** - Подключение к Supabase
```python
# Основные функции:
- get_supabase_client()  # Получение клиента
- test_connection()      # Проверка соединения
- init_database()        # Инициализация схемы
```

**queries.py** - SQL запросы и операции
```python
# Участники:
- create_participant()
- get_participant_by_telegram_id()
- update_participant_station()
- get_all_active_participants()

# Мероприятия:
- create_event()
- get_active_event()
- update_event_status()

# Сообщения админам:
- create_admin_message()
- get_unresolved_messages()
```

### 4. Utils (`src/utils/`)

**scheduler.py** - Планировщик задач
```python
class EventScheduler:
    def start_event_timer(start_time: datetime)
    def schedule_station_broadcast(station_number: int)
    def stop_all_tasks()
    def get_remaining_time() -> timedelta
```

**csv_handler.py** - Работа с CSV файлами
```python
class RouteManager:
    def load_routes_from_csv(file_path: str)
    def validate_routes()
    def get_participant_route(participant_number: int)
    def generate_routes_report()
```

**text_manager.py** - Управление текстами
```python
class TextManager:
    def get_station_message(station_id: str, participant: Participant)
    def get_welcome_message(participant_number: int)
    def get_completion_message()
    def format_participant_info(participant: Participant)
```

**logger.py** - Логирование
```python
# Конфигурация логгера с ротацией файлов
# Отправка критических ошибок админам
# Структурированное логирование событий
```

### 5. Middleware (`src/middleware/`)

**auth.py** - Авторизация
```python
class AdminAuthMiddleware:
    def __call__(handler, event, data)
    def is_admin(telegram_id: int) -> bool
```

**rate_limit.py** - Ограничение запросов
```python
class RateLimitMiddleware:
    def __call__(handler, event, data)
    def check_rate_limit(telegram_id: int) -> bool
```

## 🔄 Поток данных

### Регистрация участника:
1. Пользователь отправляет `/start`
2. `participant.py::handle_start()` обрабатывает команду
3. `queries.py::create_participant()` создает запись в БД
4. `csv_handler.py::get_participant_route()` получает маршрут
5. Отправка приветственного сообщения с меню

### Запуск мероприятия:
1. Админ отправляет `/start_event HH:MM`
2. `admin.py::handle_start_event()` валидирует время
3. `queries.py::create_event()` создает событие в БД
4. `scheduler.py::start_event_timer()` запускает таймер
5. Массовая рассылка уведомления о старте
6. Планирование рассылок станций

### Автоматическая рассылка:
1. `scheduler.py` срабатывает по таймеру
2. `queries.py::get_all_active_participants()` получает участников
3. `text_manager.py::get_station_message()` формирует сообщения
4. Batch отправка сообщений (по 30 участников)
5. Обновление current_station для всех участников
6. Планирование следующей рассылки

## 🛡️ Обработка ошибок

### Уровни ошибок:
1. **INFO** - обычные события (регистрация, команды)
2. **WARNING** - потенциальные проблемы (повторная регистрация)
3. **ERROR** - ошибки выполнения (сбой БД, ошибка API)
4. **CRITICAL** - критические сбои (падение бота)

### Стратегии восстановления:
1. **Retry механизм** для отправки сообщений (3 попытки)
2. **Graceful degradation** при недоступности БД
3. **State recovery** при перезапуске бота
4. **Admin notifications** о критических ошибках

## 📊 Производительность

### Оптимизации:
1. **Connection pooling** для Supabase
2. **Batch operations** для массовых операций
3. **Caching** маршрутов в памяти
4. **Async/await** для всех I/O операций
5. **Database indexing** для быстрых запросов

### Ограничения Telegram API:
- Максимум 30 сообщений в секунду
- Batch рассылка с задержками
- Обработка rate limit ошибок

## 🔧 Конфигурация

### Переменные окружения:
```bash
# Обязательные
BOT_TOKEN=              # Токен Telegram бота
SUPABASE_URL=           # URL Supabase проекта
SUPABASE_KEY=           # API ключ Supabase
ADMIN_IDS=              # ID администраторов (через запятую)

# Опциональные
LOG_LEVEL=INFO          # Уровень логирования
PORT=8000               # Порт для webhook
SURVEY_URL=             # Ссылка на анкету
BATCH_SIZE=30           # Размер batch для рассылки
RETRY_ATTEMPTS=3        # Количество попыток retry
```

### Настройки мероприятия:
```json
{
  "station_duration_minutes": 6,
  "total_stations": 9,
  "max_participants": 150,
  "batch_send_delay": 1.0
}
```

## 🚀 Масштабирование

### Горизонтальное масштабирование:
- Stateless архитектура позволяет запуск нескольких инстансов
- Shared state в Supabase
- Load balancing через Railway

### Вертикальное масштабирование:
- Увеличение размеров instance на Railway
- Оптимизация запросов к БД
- Тюнинг производительности Python

---

*Документ описывает архитектуру версии 1.0 проекта* 