import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    )

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