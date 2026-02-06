# TODO настроить логирование (слабенькое, но есть)
# TODO настроить обработку отключения api ключа
# TODO более удобный ввод настроек
# TODO сделать так чтобы при выводе задачи выводилась и время и дата если они есть
# TODO расставить коментарии


#FIXME спешит на 5 минут почему-то (на сервере)

import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers.commands import router as commands_router
from handlers.callbacks import router as callbacks_router
from notifications import notification_loop

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация роутеров обработчиков
dp.include_router(commands_router)
dp.include_router(callbacks_router)


async def main():
    """Главная функция запуска бота"""
    # Инициализация БД
    init_db()
    logger.info("Database initialized")
    
    # Запуск цикла уведомлений
    asyncio.create_task(notification_loop())
    logger.info("Notification loop started")
    
    # Запуск polling
    logger.info("Bot started polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("бот начал работу")
    asyncio.run(main())
