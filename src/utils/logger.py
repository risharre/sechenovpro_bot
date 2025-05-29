"""
Система логирования для Sechenov Pro Bot
"""

import sys
from pathlib import Path
from loguru import logger
from ..bot.config import Config


def setup_logger():
    """Настройка системы логирования"""
    
    # Удаляем стандартный handler
    logger.remove()
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Консольный вывод
    logger.add(
        sys.stdout,
        level=Config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Файл для всех логов
    logger.add(
        log_dir / "bot.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    # Файл только для ошибок
    logger.add(
        log_dir / "errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="5 MB",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("📝 Система логирования настроена")


def get_logger(name: str):
    """Получение логгера для модуля"""
    return logger.bind(name=name)


# Инициализируем логирование при импорте
setup_logger() 