"""
Обработчики команд администраторов
"""

import csv
import io
from datetime import datetime
from typing import List

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from ..bot.config import Config
from ..database.queries import get_db_queries
from ..utils.text_manager import get_text_manager
from ..utils.scheduler import get_event_scheduler
from ..utils.logger import get_logger
from .menu import get_admin_menu
from .participant import (
    broadcast_to_all_participants,
    broadcast_station_to_all,
    send_event_start_notification,
    send_event_completion_notification
)

logger = get_logger(__name__)
router = Router()

# Инициализация компонентов
db = get_db_queries()
text_manager = get_text_manager()
scheduler = get_event_scheduler()


def is_admin(telegram_username: str) -> bool:
    """Проверка, является ли пользователь администратором"""
    if not telegram_username:
        return False
    
    admin_usernames = [username.lower().strip('@') for username in Config.ADMIN_USERNAMES]
    user_username = telegram_username.lower().strip('@')
    
    return user_username in admin_usernames


@router.message(Command("start_event"))
async def cmd_start_event(message: Message):
    """Команда /start_event - запуск мероприятия"""
    try:
        user = message.from_user
        if not user or not user.username:
            await message.answer("❌ Для использования админских команд необходим username")
            return
        
        if not is_admin(user.username):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        logger.info(f"Команда /start_event от админа @{user.username}")
        
        # Проверяем, есть ли уже активное мероприятие
        existing_event = await db.get_active_event()
        if existing_event:
            await message.answer("⚠️ Мероприятие уже активно! Используйте /stop_event для остановки")
            return
        
        # Получаем всех участников
        participants = await db.get_all_active_participants()
        if not participants:
            await message.answer("❌ Нет зарегистрированных участников")
            return
        
        # Создаем новое мероприятие
        event = await db.create_event(user.id)
        if not event:
            await message.answer("❌ Ошибка создания мероприятия")
            return
        
        # Настраиваем планировщик с callback функциями
        await scheduler.setup_event_schedule(
            on_station_start=_on_station_start,
            on_transition_start=_on_transition_start,
            on_event_complete=_on_event_complete
        )
        
        # Запускаем планировщик
        await scheduler.start_event()
        
        # Отправляем уведомление о старте всем участникам
        start_message = text_manager.format_event_started_message()
        sent_count, failed_count = await broadcast_to_all_participants(start_message)
        
        # Запускаем первую станцию
        await broadcast_station_to_all(1)
        
        # Уведомляем админа об успехе
        success_message = text_manager.format_event_start_success(sent_count)
        await message.answer(success_message, reply_markup=get_admin_menu())
        
        logger.info(f"Мероприятие запущено админом @{user.username}: {sent_count} участников уведомлено")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /start_event: {e}")
        await message.answer("❌ Произошла ошибка при запуске мероприятия")


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Команда /status - статус мероприятия"""
    try:
        user = message.from_user
        if not user or not user.username:
            await message.answer("❌ Для использования админских команд необходим username")
            return
        
        if not is_admin(user.username):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        logger.info(f"Команда /status от админа @{user.username}")
        
        # Получаем статистику мероприятия
        stats = await db.get_event_statistics()
        
        if not stats:
            await message.answer("❌ Нет данных о мероприятии")
            return
        
        # Получаем время старта мероприятия
        event_start_time = None
        active_event = await db.get_active_event()
        if active_event:
            event_start_time = active_event.start_time
        
        # Формируем статус сообщение
        status_message = text_manager.format_admin_status(stats, event_start_time)
        
        await message.answer(status_message, reply_markup=get_admin_menu())
        
    except Exception as e:
        logger.error(f"Ошибка в команде /status: {e}")
        await message.answer("❌ Произошла ошибка при получении статуса")


@router.message(Command("stop_event"))
async def cmd_stop_event(message: Message):
    """Команда /stop_event - остановка мероприятия"""
    try:
        user = message.from_user
        if not user or not user.username:
            await message.answer("❌ Для использования админских команд необходим username")
            return
        
        if not is_admin(user.username):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        logger.info(f"Команда /stop_event от админа @{user.username}")
        
        # Проверяем, есть ли активное мероприятие
        active_event = await db.get_active_event()
        if not active_event:
            await message.answer("⚠️ Нет активного мероприятия")
            return
        
        # Останавливаем планировщик
        await scheduler.stop_event()
        
        # Останавливаем мероприятие в базе данных
        await db.stop_event(active_event.id)
        
        # Уведомляем участников об остановке
        stop_message = "🛑 Мероприятие остановлено организаторами.\n\nСпасибо за участие!"
        sent_count, failed_count = await broadcast_to_all_participants(stop_message)
        
        # Уведомляем админа об успехе
        success_message = text_manager.format_event_stop_success()
        await message.answer(success_message, reply_markup=get_admin_menu())
        
        logger.info(f"Мероприятие остановлено админом @{user.username}")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /stop_event: {e}")
        await message.answer("❌ Произошла ошибка при остановке мероприятия")


@router.message(Command("report"))
async def cmd_report(message: Message):
    """Команда /report - экспорт отчета участников"""
    try:
        user = message.from_user
        if not user or not user.username:
            await message.answer("❌ Для использования админских команд необходим username")
            return
        
        if not is_admin(user.username):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        logger.info(f"Команда /report от админа @{user.username}")
        
        # Получаем данные участников для экспорта
        csv_data = await db.export_participants_csv()
        
        if not csv_data:
            await message.answer("❌ Нет данных для экспорта")
            return
        
        # Создаем CSV файл в памяти
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "participant_number", "telegram_id", "telegram_username", 
            "full_name", "current_station", "route", "registration_date", 
            "last_updated", "is_active"
        ])
        
        writer.writeheader()
        writer.writerows(csv_data)
        
        # Конвертируем в байты
        csv_content = output.getvalue().encode('utf-8-sig')  # BOM для Excel
        output.close()
        
        # Генерируем имя файла с текущей датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sechenov_pro_participants_{timestamp}.csv"
        
        # Создаем файл для отправки
        csv_file = BufferedInputFile(
            csv_content,
            filename=filename
        )
        
        # Отправляем файл
        await message.answer_document(
            csv_file,
            caption=f"📊 Отчет участников мероприятия\n\n"
                   f"📅 Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                   f"👥 Участников: {len(csv_data)}"
        )
        
        logger.info(f"Отчет отправлен админу @{user.username}: {len(csv_data)} участников")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /report: {e}")
        await message.answer("❌ Произошла ошибка при создании отчета")


@router.callback_query(F.data == "admin_status")
async def callback_admin_status(callback: CallbackQuery):
    """Callback для получения статуса через меню"""
    try:
        user = callback.from_user
        if not user or not user.username:
            await callback.answer("❌ Необходим username")
            return
        
        if not is_admin(user.username):
            await callback.answer("❌ Нет прав администратора")
            return
        
        # Получаем статистику
        stats = await db.get_event_statistics()
        
        if not stats:
            await callback.message.edit_text(
                "❌ Нет данных о мероприятии",
                reply_markup=get_admin_menu()
            )
            return
        
        # Получаем время старта
        event_start_time = None
        active_event = await db.get_active_event()
        if active_event:
            event_start_time = active_event.start_time
        
        # Формируем статус
        status_message = text_manager.format_admin_status(stats, event_start_time)
        
        await callback.message.edit_text(
            status_message,
            reply_markup=get_admin_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в callback_admin_status: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery):
    """Callback для создания широковещательного сообщения"""
    try:
        user = callback.from_user
        if not user or not user.username:
            await callback.answer("❌ Необходим username")
            return
        
        if not is_admin(user.username):
            await callback.answer("❌ Нет прав администратора")
            return
        
        broadcast_text = """📢 Создание объявления

Отправьте следующим сообщением текст для рассылки всем участникам.

Для отмены используйте /cancel"""
        
        await callback.message.edit_text(broadcast_text)
        await callback.answer()
        
        # TODO: Здесь можно добавить состояние FSM для ожидания текста сообщения
        
    except Exception as e:
        logger.error(f"Ошибка в callback_admin_broadcast: {e}")
        await callback.answer("❌ Произошла ошибка")


# =================== CALLBACK ФУНКЦИИ ДЛЯ ПЛАНИРОВЩИКА ===================

async def _on_station_start(station_number: int):
    """Callback при начале станции"""
    try:
        logger.info(f"Начало станции {station_number}")
        
        # Отправляем уведомления всем участникам
        sent_count = await broadcast_station_to_all(station_number)
        
        # Уведомляем админов
        admin_message = f"🏁 Станция {station_number}/9 запущена\n👥 Уведомлено участников: {sent_count}"
        await _notify_all_admins(admin_message)
        
    except Exception as e:
        logger.error(f"Ошибка в _on_station_start для станции {station_number}: {e}")


async def _on_transition_start(from_station: int, to_station: int):
    """Callback при начале перехода"""
    try:
        logger.info(f"Начало перехода со станции {from_station} на {to_station}")
        
        # Отправляем уведомления о переходе
        from .participant import broadcast_transition_to_all
        sent_count = await broadcast_transition_to_all(from_station, to_station)
        
        # Уведомляем админов
        admin_message = f"🚶‍♂️ Переход {from_station}→{to_station}\n👥 Уведомлено участников: {sent_count}"
        await _notify_all_admins(admin_message)
        
    except Exception as e:
        logger.error(f"Ошибка в _on_transition_start {from_station}→{to_station}: {e}")


async def _on_event_complete():
    """Callback при завершении мероприятия"""
    try:
        logger.info("Мероприятие завершено")
        
        # Завершаем мероприятие в базе данных
        active_event = await db.get_active_event()
        if active_event:
            await db.complete_event(active_event.id)
        
        # Отправляем уведомления о завершении
        completion_message = text_manager.format_event_completed_message()
        sent_count, failed_count = await broadcast_to_all_participants(completion_message)
        
        # Уведомляем админов
        admin_message = f"🎊 Мероприятие завершено!\n👥 Уведомлено участников: {sent_count}"
        await _notify_all_admins(admin_message)
        
    except Exception as e:
        logger.error(f"Ошибка в _on_event_complete: {e}")


async def _notify_all_admins(message_text: str):
    """Уведомление всех админов"""
    try:
        from aiogram import Bot
        from ..bot.config import Config
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        # Получаем всех участников и проверяем, кто из них админ
        participants = await db.get_all_active_participants()
        admin_count = 0
        
        for participant in participants:
            if participant.telegram_username and is_admin(participant.telegram_username):
                try:
                    await bot.send_message(participant.telegram_id, message_text)
                    admin_count += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения админу {participant.telegram_id}: {e}")
        
        if admin_count > 0:
            logger.info(f"Уведомлено {admin_count} админов")
        else:
            logger.warning("Не найдено админов для уведомления")
        
        await bot.session.close()
            
    except Exception as e:
        logger.error(f"Ошибка уведомления админов: {e}")


# =================== ДОПОЛНИТЕЛЬНЫЕ АДМИНСКИЕ КОМАНДЫ ===================

@router.message(Command("participants"))
async def cmd_participants(message: Message):
    """Команда для просмотра списка участников"""
    try:
        user = message.from_user
        if not user or not user.username:
            await message.answer("❌ Для использования админских команд необходим username")
            return
        
        if not is_admin(user.username):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        participants = await db.get_all_active_participants()
        
        if not participants:
            await message.answer("👥 Нет зарегистрированных участников")
            return
        
        # Группируем участников по станциям
        station_groups = {}
        for participant in participants:
            station = participant.current_station
            if station not in station_groups:
                station_groups[station] = []
            station_groups[station].append(participant)
        
        # Формируем сообщение
        response_text = f"👥 Всего участников: {len(participants)}\n\n"
        
        for station in sorted(station_groups.keys()):
            participants_list = station_groups[station]
            station_name = "Ожидание старта" if station == 0 else f"Станция {station}"
            
            response_text += f"📍 {station_name}: {len(participants_list)} чел.\n"
            
            # Показываем первых 5 участников
            for i, participant in enumerate(participants_list[:5]):
                response_text += f"  • #{participant.participant_number:03d} {participant.full_name}\n"
            
            if len(participants_list) > 5:
                response_text += f"  ... и еще {len(participants_list) - 5} участников\n"
            
            response_text += "\n"
        
        await message.answer(response_text[:4096])  # Ограничение Telegram
        
    except Exception as e:
        logger.error(f"Ошибка в команде /participants: {e}")
        await message.answer("❌ Произошла ошибка при получении списка участников")


@router.message(Command("help_admin"))
async def cmd_help_admin(message: Message):
    """Справка по админским командам"""
    try:
        user = message.from_user
        if not user or not user.username:
            await message.answer("❌ Для использования админских команд необходим username")
            return
        
        if not is_admin(user.username):
            await message.answer("❌ У вас нет прав администратора")
            return
        
        help_text = """🔧 Админские команды:

/start_event - Запустить мероприятие
/status - Статус мероприятия  
/stop_event - Остановить мероприятие
/report - Экспорт участников в CSV
/participants - Список участников
/help_admin - Эта справка

📊 Мероприятие длится 70 минут:
• 9 станций по 6 минут
• 8 переходов по 2 минуты  
• Автоматические уведомления

⚠️ Важно:
• Перед запуском убедитесь в регистрации участников
• Во время мероприятия следите за статусом
• При проблемах используйте /stop_event"""
        
        await message.answer(help_text, reply_markup=get_admin_menu())
        
    except Exception as e:
        logger.error(f"Ошибка в команде /help_admin: {e}")
        await message.answer("❌ Произошла ошибка") 