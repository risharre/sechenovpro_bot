#!/usr/bin/env python3
"""
Sechenov Pro Network Event Bot
Точка входа приложения
"""

import asyncio
import sys
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.bot.main import main

if __name__ == "__main__":
    print("🚀 Запуск Sechenov Pro Network Event Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1) 