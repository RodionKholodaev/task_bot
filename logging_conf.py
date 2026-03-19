import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():

    os.makedirs("logs", exist_ok=True)
    
    # когда файл достигает 5 МБ, он переименовывается и создается новый. храним до 3 старых файлов
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=10*1024*1024,  # 10 МБ
        backupCount=3,          # хранить 3 старых файла
        encoding='utf-8'
    )
    
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    ))

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    )

    # ставим WARNING, чтобы видеть только критические ошибки
    quiet_loggers = [
        "openai",      
        "httpx",       
        "httpcore",    
        "aiogram",     
        "sqlalchemy",  
        "apscheduler", 
        "yookassa",    
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