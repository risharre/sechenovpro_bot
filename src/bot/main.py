"""
Главный модуль бота
"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .config import Config
from ..handlers import participant, admin
from ..database.connection import get_supabase_client, test_connection
from ..utils.logger import get_logger
from ..utils.scheduler import get_event_scheduler

logger = get_logger(__name__)

# Создаем экземпляр бота
bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаем диспетчер
dp = Dispatcher()


async def set_bot_commands():
    """Установка команд бота в меню"""
    commands = [
        BotCommand(command="start", description="Регистрация на мероприятие"),
        BotCommand(command="start_event", description="🔧 Запустить мероприятие (админ)"),
        BotCommand(command="status", description="🔧 Статус мероприятия (админ)"),
        BotCommand(command="stop_event", description="🔧 Остановить мероприятие (админ)"),
        BotCommand(command="report", description="🔧 Экспорт участников (админ)"),
        BotCommand(command="participants", description="🔧 Список участников (админ)"),
        BotCommand(command="help_admin", description="🔧 Справка для админов (админ)")
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Команды бота установлены")


async def on_startup():
    """Действия при запуске бота"""
    try:
        logger.info("🚀 Запуск Sechenov Pro Bot...")
        
        # Проверяем подключение к базе данных
        logger.info("🔌 Проверка подключения к базе данных...")
        if not await test_connection():
            logger.error("❌ Не удалось подключиться к базе данных")
            raise ConnectionError("Database connection failed")
        
        logger.info("✅ Подключение к базе данных успешно")
        
        # Устанавливаем команды бота
        await set_bot_commands()
        
        # Инициализируем планировщик
        scheduler = get_event_scheduler()
        logger.info("⏰ Планировщик инициализирован")
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username}")
        logger.info(f"📋 Конфигурация загружена")
        logger.info(f"👑 Админы: {', '.join(Config.ADMIN_USERNAMES)}")
        
        logger.info("✅ Sechenov Pro Bot успешно запущен!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise


async def on_shutdown():
    """Действия при остановке бота"""
    try:
        logger.info("🛑 Остановка Sechenov Pro Bot...")
        
        # Останавливаем планировщик
        scheduler = get_event_scheduler()
        await scheduler.stop_event()
        logger.info("⏰ Планировщик остановлен")
        
        # Закрываем сессию бота
        await bot.session.close()
        logger.info("🔌 Сессия бота закрыта")
        
        logger.info("✅ Sechenov Pro Bot остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")


def setup_handlers():
    """Настройка обработчиков"""
    # Регистрируем роутеры
    dp.include_router(participant.router)
    dp.include_router(admin.router)
    
    logger.info("📡 Обработчики зарегистрированы")


async def main():
    """Главная функция запуска бота"""
    try:
        # Настраиваем обработчики
        setup_handlers()
        
        # Регистрируем события startup/shutdown
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Запускаем бота
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        logger.info("🏁 Завершение работы бота")


if __name__ == "__main__":
    asyncio.run(main()) 