import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    
    # 1. Создаем файловый обработчик
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=10*1024*1024,  # 10 МБ (в комментарии было 5, тут 10 — не критично)
        backupCount=3,
        encoding='utf-8'
    )
    
    file_handler.setLevel(logging.ERROR) # В файл пишем только ERROR и CRITICAL
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    ))

    # 2. Настраиваем консольный вывод через basicConfig
    logging.basicConfig(
        level=logging.DEBUG, # В консоль пишем всё от DEBUG и выше
        format="%(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s",
        handlers=[
            logging.StreamHandler(), # Это вывод в консоль
            file_handler             # <--- Добавляем наш файл сюда!
        ]
    )

    # Заглушаем шумные библиотеки
    quiet_loggers = [
        "openai", "httpx", "httpcore", "aiogram", 
        "sqlalchemy", "apscheduler", "yookassa", "aiosqlite"
    ]

    for logger_name in quiet_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Отдельный совет по SQLAlchemy:
    # Если начнешь ловить ошибки в БД, временно поставь ему INFO или DEBUG:
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# уровни по возрастанию важности:
# DEBUG < INFO < WARNING < ERROR < CRITICAL

# как работает формат:
# format="%(asctime)s | %(levelname)s | %(name)s | %(message)s":
# 2026-02-28 21:40:15 | INFO | handlers.task | Получено сообщение

# методы для разных уровней логов:

# debug()
# Техническая информация для разработчика.
# В проде обычно выключен.
# logger.debug("")

# info()
# Нормальные бизнес-события.
# logger.info("Создана новая задача")

# warning()
# Что-то странное, но не ошибка.
# Очень полезный уровень.
# logger.warning("")
# Система работает, но поведение подозрительное.

# error()
# Операция не удалась.
# logger.error("Ошибка сохранения задачи")
# Без traceback.

# exception()
# Используется только внутри except.
# Автоматически добавляет traceback.
# try:
#     save_task(task)
# except Exception:
#     logger.exception("Ошибка при сохранении задачи")

# critical()
# Что-то фатальное. Система не может продолжать работу.
# logger.critical("База данных недоступна")
# Используется редко.