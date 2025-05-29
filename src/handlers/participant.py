"""
Обработчики команд участников
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from typing import Optional

from ..database.queries import get_db_queries
from ..utils.text_manager import get_text_manager
from ..utils.csv_handler import get_csv_handler
from ..utils.scheduler import get_event_scheduler
from ..utils.logger import get_logger
from .menu import get_participant_menu

logger = get_logger(__name__)
router = Router()

# Инициализация компонентов
db = get_db_queries()
text_manager = get_text_manager()
csv_handler = get_csv_handler()
scheduler = get_event_scheduler()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start - регистрация участника"""
    try:
        user = message.from_user
        if not user:
            await message.answer("❌ Ошибка получения данных пользователя")
            return
        
        telegram_id = user.id
        telegram_username = user.username or "unknown"
        full_name = user.full_name or f"User {telegram_id}"
        
        logger.info(f"Команда /start от пользователя {telegram_id} (@{telegram_username})")
        
        # Проверяем, зарегистрирован ли уже участник
        existing_participant = await db.get_participant_by_telegram_id(telegram_id)
        
        if existing_participant:
            # Участник уже зарегистрирован
            welcome_text = text_manager.format_already_registered_message(
                existing_participant.participant_number,
                existing_participant.current_station
            )
            keyboard = get_participant_menu()
            await message.answer(welcome_text, reply_markup=keyboard)
            return
        
        # Получаем маршрут для нового участника
        route = csv_handler.get_next_route()
        if not route:
            await message.answer("❌ Извините, все места на мероприятии заняты")
            return
        
        # Создаем нового участника
        participant = await db.create_participant(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            full_name=full_name,
            route=route
        )
        
        if not participant:
            await message.answer("❌ Ошибка регистрации. Попробуйте позже")
            return
        
        # Отправляем приветственное сообщение
        welcome_text = text_manager.format_welcome_message(participant.participant_number)
        keyboard = get_participant_menu()
        
        await message.answer(welcome_text, reply_markup=keyboard)
        
        logger.info(f"Зарегистрирован участник #{participant.participant_number}: {full_name}")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже")


@router.callback_query(F.data == "current_station")
async def callback_current_station(callback: CallbackQuery):
    """Информация о текущей станции"""
    try:
        user = callback.from_user
        if not user:
            await callback.answer("❌ Ошибка получения данных")
            return
        
        participant = await db.get_participant_by_telegram_id(user.id)
        if not participant:
            await callback.answer("❌ Вы не зарегистрированы. Используйте /start")
            return
        
        # Получаем время старта мероприятия
        event_start_time = None
        active_event = await db.get_active_event()
        if active_event:
            event_start_time = active_event.start_time
        
        # Получаем букву станции
        station_letter = text_manager.get_station_letter_by_number(participant.current_station)
        
        # Формируем сообщение
        station_info = text_manager.format_current_station_info(
            participant.participant_number,
            participant.current_station,
            station_letter,
            event_start_time
        )
        
        await callback.message.edit_text(
            station_info,
            reply_markup=get_participant_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_current_station: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "next_station")
async def callback_next_station(callback: CallbackQuery):
    """Информация о следующей станции"""
    try:
        user = callback.from_user
        if not user:
            await callback.answer("❌ Ошибка получения данных")
            return
        
        participant = await db.get_participant_by_telegram_id(user.id)
        if not participant:
            await callback.answer("❌ Вы не зарегистрированы. Используйте /start")
            return
        
        # Получаем букву следующей станции
        next_station_number = participant.current_station + 1
        next_letter = text_manager.get_station_letter_by_number(next_station_number)
        
        # Формируем сообщение
        next_info = text_manager.format_next_station_info(
            participant.current_station,
            next_letter
        )
        
        await callback.message.edit_text(
            next_info,
            reply_markup=get_participant_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_next_station: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "full_schedule")
async def callback_full_schedule(callback: CallbackQuery):
    """Полное расписание мероприятия"""
    try:
        # Получаем время старта мероприятия
        event_start_time = None
        active_event = await db.get_active_event()
        if active_event:
            event_start_time = active_event.start_time
        
        # Формируем расписание
        schedule_text = text_manager.format_full_schedule(event_start_time)
        
        await callback.message.edit_text(
            schedule_text,
            reply_markup=get_participant_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_full_schedule: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "participant_info")
async def callback_participant_info(callback: CallbackQuery):
    """Информация участника"""
    try:
        user = callback.from_user
        if not user:
            await callback.answer("❌ Ошибка получения данных")
            return
        
        participant = await db.get_participant_by_telegram_id(user.id)
        if not participant:
            await callback.answer("❌ Вы не зарегистрированы. Используйте /start")
            return
        
        # Получаем время старта мероприятия
        event_start_time = None
        active_event = await db.get_active_event()
        if active_event:
            event_start_time = active_event.start_time
        
        # Формируем информацию участника
        participant_info = text_manager.format_participant_info(
            participant.participant_number,
            participant.current_station,
            participant.route,
            event_start_time
        )
        
        await callback.message.edit_text(
            participant_info,
            reply_markup=get_participant_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_participant_info: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "contact_organizer")
async def callback_contact_organizer(callback: CallbackQuery):
    """Связь с организатором"""
    try:
        contact_info = text_manager.format_contact_organizer()
        
        await callback.message.edit_text(
            contact_info,
            reply_markup=get_participant_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_contact_organizer: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    try:
        user = callback.from_user
        if not user:
            await callback.answer("❌ Ошибка получения данных")
            return
        
        participant = await db.get_participant_by_telegram_id(user.id)
        if not participant:
            welcome_text = "🤖 Добро пожаловать! Используйте /start для регистрации"
        else:
            welcome_text = f"👤 Участник #{participant.participant_number:03d}\n📊 Станция: {participant.current_station}/9\n\nВыберите действие:"
        
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_participant_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_back_to_menu: {e}")
        await callback.answer("❌ Произошла ошибка")


# =================== ФУНКЦИИ ДЛЯ РАССЫЛКИ ===================

async def send_station_notification(telegram_id: int, station_number: int):
    """Отправка уведомления о новой станции участнику"""
    try:
        from aiogram import Bot
        from ..bot.config import Config
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        station_letter = text_manager.get_station_letter_by_number(station_number)
        message_text = text_manager.format_station_message(station_number, station_letter)
        
        await bot.send_message(telegram_id, message_text)
        
        # Обновляем текущую станцию участника в БД
        await db.update_participant_station(telegram_id, station_number)
        
        logger.info(f"Отправлено уведомление о станции {station_number} участнику {telegram_id}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о станции {station_number} участнику {telegram_id}: {e}")


async def send_transition_notification(telegram_id: int, from_station: int, to_station: int):
    """Отправка уведомления о переходе участнику"""
    try:
        from aiogram import Bot
        from ..bot.config import Config
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        to_letter = text_manager.get_station_letter_by_number(to_station)
        message_text = text_manager.format_transition_message(from_station, to_station, to_letter)
        
        await bot.send_message(telegram_id, message_text)
        
        logger.info(f"Отправлено уведомление о переходе {from_station}→{to_station} участнику {telegram_id}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о переходе участнику {telegram_id}: {e}")


async def send_event_start_notification(telegram_id: int):
    """Отправка уведомления о старте мероприятия участнику"""
    try:
        from aiogram import Bot
        from ..bot.config import Config
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        message_text = text_manager.format_event_started_message()
        
        await bot.send_message(telegram_id, message_text)
        
        logger.info(f"Отправлено уведомление о старте мероприятия участнику {telegram_id}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о старте участнику {telegram_id}: {e}")


async def send_event_completion_notification(telegram_id: int):
    """Отправка уведомления о завершении мероприятия участнику"""
    try:
        from aiogram import Bot
        from ..bot.config import Config
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        message_text = text_manager.format_event_completed_message()
        
        await bot.send_message(telegram_id, message_text)
        
        logger.info(f"Отправлено уведомление о завершении мероприятия участнику {telegram_id}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о завершении участнику {telegram_id}: {e}")


# =================== МАССОВЫЕ РАССЫЛКИ ===================

async def broadcast_to_all_participants(message_text: str):
    """Массовая рассылка всем участникам"""
    try:
        from aiogram import Bot
        from ..bot.config import Config
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        participants = await db.get_all_active_participants()
        sent_count = 0
        failed_count = 0
        
        for participant in participants:
            try:
                await bot.send_message(participant.telegram_id, message_text)
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения участнику {participant.telegram_id}: {e}")
                failed_count += 1
        
        logger.info(f"Массовая рассылка завершена: {sent_count} успешно, {failed_count} ошибок")
        
        await bot.session.close()
        return sent_count, failed_count
        
    except Exception as e:
        logger.error(f"Ошибка массовой рассылки: {e}")
        return 0, 0


async def broadcast_station_to_all(station_number: int):
    """Массовая рассылка уведомления о станции всем участникам"""
    try:
        participants = await db.get_all_active_participants()
        sent_count = 0
        
        for participant in participants:
            await send_station_notification(participant.telegram_id, station_number)
            sent_count += 1
        
        logger.info(f"Разослано уведомление о станции {station_number} для {sent_count} участников")
        return sent_count
        
    except Exception as e:
        logger.error(f"Ошибка рассылки уведомления о станции {station_number}: {e}")
        return 0


async def broadcast_transition_to_all(from_station: int, to_station: int):
    """Массовая рассылка уведомления о переходе всем участникам"""
    try:
        participants = await db.get_all_active_participants()
        sent_count = 0
        
        for participant in participants:
            await send_transition_notification(participant.telegram_id, from_station, to_station)
            sent_count += 1
        
        logger.info(f"Разослано уведомление о переходе {from_station}→{to_station} для {sent_count} участников")
        return sent_count
        
    except Exception as e:
        logger.error(f"Ошибка рассылки уведомления о переходе: {e}")
        return 0 