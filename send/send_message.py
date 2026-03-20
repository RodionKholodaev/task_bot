import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from keyboards import new_main_keyboard

# Настройки
TOKEN = "8323121260:AAFTnun59sHfaawIw_LGhymLnVsoO_EfV9I"
DB_URL = "sqlite+aiosqlite:///tasks.db"

MESSAGE_TEXT = "Прошу прощения, бот был временно недоступен из-за блокировок"

NEW_VERSION_TEXT = (
    "**Обновление!**\n\n"
    "Появился профиль пользователя \"🧑 Профиль\"\n\n"
    "В нем в разделе \"⏰ Настройка уведомлений\" можно указать время ежедневных напоминаний и часовой пояс.\n\n"
    "В разделе \"📝 О себе\" вы можете указать информацию, которую нужно учитывать боту при записи ваших задач и покупок "
    "(например, можно указать сколько времени у вас уходит на разные классы задач для более точной классификации, "
    "или попросить всегда делать описание задачи в четком формате)."
)

async def get_user_ids(session_pool):
    """Извлекает все user_id из таблицы user_settings"""
    async with session_pool() as session:
        query = text("SELECT user_id FROM user_settings")
        result = await session.execute(query)
        return [row[0] for row in result.fetchall()]

async def main():
    engine = create_async_engine(DB_URL)
    session_pool = async_sessionmaker(engine, expire_on_commit=False)
    
    # Используем MARKDOWN (или HTML, если будут ошибки с символами)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    
    try:
        user_ids = await get_user_ids(session_pool)
        print(f"Найдено пользователей: {len(user_ids)}. Начинаю рассылку...")

        count = 0
        for user_id in user_ids:
            try:
                # Отправляем первое сообщение
                await bot.send_message(chat_id=user_id, text=MESSAGE_TEXT, reply_markup=new_main_keyboard())
                
                # Небольшая пауза между сообщениями одному пользователю
                await asyncio.sleep(0.1)
                
                # Отправляем второе сообщение (с обновлением)
                await bot.send_message(chat_id=user_id, text=NEW_VERSION_TEXT, reply_markup=new_main_keyboard())
                
                count += 1
                # Лимит Telegram — 30 сообщений в секунду суммарно
                await asyncio.sleep(0.05) 
                
            except TelegramRetryAfter as e:
                print(f"Лимит превышен. Ждем {e.retry_after} сек.")
                await asyncio.sleep(e.retry_after)
                # Повторная попытка (упрощенно)
                await bot.send_message(user_id, MESSAGE_TEXT, reply_markup=new_main_keyboard())
                await bot.send_message(user_id, NEW_VERSION_TEXT, reply_markup=new_main_keyboard())
                
            except TelegramForbiddenError:
                print(f"Пользователь {user_id} заблокировал бота.")
            except Exception as e:
                print(f"Не удалось отправить {user_id}: {e}")

        print(f"Рассылка завершена! Успешно обработано пользователей: {count}")

    finally:
        await bot.session.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())