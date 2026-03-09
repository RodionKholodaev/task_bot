import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from config import BOT_TOKEN
if not BOT_TOKEN: raise ValueError("нет токена бота")


from db.task_repository import TaskRepository
from db.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)


async def notification_loop():
    while True:
        now_utc = datetime.utcnow()

        users = UserRepository.get_all_users()
        if users is None:
            logger.info("Нет пользователей в боте. Некому делать напоминания")
            continue
        for u in users:
            
            if u.notify_time is None and u.utc_offset is None:
                continue

            local_now = now_utc + timedelta(hours=u.utc_offset) # type: ignore
            local_date = local_now.date()
            local_time = local_now.time().replace(second=0, microsecond=0)

            # ========= 1. ЕЖЕДНЕВНОЕ УВЕДОМЛЕНИЕ =========
            if (
                local_time.hour == u.notify_time.hour and
                local_time.minute == u.notify_time.minute
            ):
                tasks = TaskRepository.get_tasks_for_day(u.user_id, local_date) # type: ignore
                if tasks:
                    text = "🔔 Задачи на сегодня:\n" + "\n".join(
                        f"- {t.description}" for t in tasks
                    )
                    await bot.send_message(u.user_id, text) # type: ignore

            # ========= 2. НАПОМИНАНИЯ ПО ЗАДАЧАМ =========

            remind_tasks = TaskRepository.get_tasks_to_remind(u.user_id) # type: ignore

            for task in remind_tasks:
                if task.remind_time is not None:
                    remind_at = task.remind_time
                else:
                    remind_at = u.notify_time

                if task.remind_date is not None:
                    remind_day = task.remind_date
                else:
                    remind_day = local_date # на самом деле это никогда не сработает, но пусть будет

                if (
                    remind_at.hour == local_time.hour and # type: ignore
                    remind_at.minute == local_time.minute and
                    remind_day==local_date
                ):
                    await bot.send_message(
                        u.user_id, # type: ignore
                        f"⏰ Напоминание:\n{task.description}"
                    )


        await asyncio.sleep(60)
