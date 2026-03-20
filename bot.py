import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
if not BOT_TOKEN: raise ValueError("нет токена бота")

from db.database import init_db, get_session

from middlewares.db import DbSessionMiddleware # middleware для проброса сессий в хендлер
from middlewares.statistic import UpdateActivityMiddleware

from handlers.commands import router as commands_router
from handlers.callbacks import router as callbacks_router

from scheduler.scheduler_config import init_scheduler, shutdown_scheduler
from scheduler.task_scheduler import load_all_jobs_from_db

from logging_conf import setup_logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# middleware для статистики
dp.update.outer_middleware(DbSessionMiddleware(get_session))
# middleware для статистики
dp.update.outer_middleware(UpdateActivityMiddleware())
# Регистрация роутеров обработчиков
dp.include_router(commands_router)
dp.include_router(callbacks_router)

async def main():
    """Главная функция запуска бота"""

    setup_logging()
    logger.info("Бот начал работу")
    
    # Инициализация БД
    await init_db() # type ignore
    
    # Инициализация планировщика
    init_scheduler()
    
    # Загрузка всех джобов из БД
    async with get_session() as s:
        await load_all_jobs_from_db(s) #type: ignore
        

    logger.info("Все джобы загружены из БД")
    
    # Запуск polling
    logger.info("Bot started polling")
    await dp.start_polling(bot)


async def on_shutdown():
    """Очистка при остановке бота"""
    shutdown_scheduler()
    await bot.session.close()
    logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(on_shutdown())