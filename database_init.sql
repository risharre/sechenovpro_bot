-- Инициализация базы данных для Sechenov Pro Network Event Bot
-- Выполните этот скрипт в SQL Editor на Supabase

-- Создание таблицы участников
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    participant_number INTEGER UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    registration_time TIMESTAMP DEFAULT NOW(),
    current_station INTEGER DEFAULT 0,
    route_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP DEFAULT NOW()
);

-- Создание таблицы мероприятий
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMP,
    is_active BOOLEAN DEFAULT false,
    current_station INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Создание таблицы сообщений администраторам
CREATE TABLE IF NOT EXISTS admin_messages (
    id SERIAL PRIMARY KEY,
    participant_id INTEGER REFERENCES participants(id),
    message_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_resolved BOOLEAN DEFAULT false
);

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_participants_telegram_id ON participants(telegram_id);
CREATE INDEX IF NOT EXISTS idx_participants_number ON participants(participant_number);
CREATE INDEX IF NOT EXISTS idx_participants_active ON participants(is_active);
CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_messages_resolved ON admin_messages(is_resolved);
CREATE INDEX IF NOT EXISTS idx_admin_messages_created ON admin_messages(created_at);

-- Добавление комментариев к таблицам
COMMENT ON TABLE participants IS 'Участники мероприятия';
COMMENT ON TABLE events IS 'Информация о мероприятиях';
COMMENT ON TABLE admin_messages IS 'Сообщения участников администраторам';

-- Добавление комментариев к столбцам
COMMENT ON COLUMN participants.telegram_id IS 'Уникальный ID пользователя в Telegram';
COMMENT ON COLUMN participants.participant_number IS 'Номер участника (001-150)';
COMMENT ON COLUMN participants.current_station IS 'Номер текущей станции (0 = не начато)';
COMMENT ON COLUMN participants.route_data IS 'Маршрут участника в формате JSON';
COMMENT ON COLUMN events.current_station IS 'Номер текущей станции мероприятия';
COMMENT ON COLUMN admin_messages.is_resolved IS 'Обработано ли сообщение администратором';

-- Проверочные запросы (можно выполнить для проверки)
-- SELECT COUNT(*) as total_participants FROM participants;
-- SELECT COUNT(*) as active_events FROM events WHERE is_active = true;
-- SELECT COUNT(*) as unresolved_messages FROM admin_messages WHERE is_resolved = false; 