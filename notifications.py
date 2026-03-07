import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from config import BOT_TOKEN

from db.task_repository import TaskRepository
from db.user_repository import UserRepository


bot = Bot(token=BOT_TOKEN)


async def notification_loop():
    while True:
        now_utc = datetime.utcnow()

        users = UserRepository.get_all_users()
 
        for u in users:
            local_now = now_utc + timedelta(hours=u.utc_offset)
            local_date = local_now.date()
            local_time = local_now.time().replace(second=0, microsecond=0)

            # ========= 1. ЕЖЕДНЕВНОЕ УВЕДОМЛЕНИЕ =========
            if (
                local_time.hour == u.notify_time.hour and
                local_time.minute == u.notify_time.minute
            ):
                tasks = TaskRepository.get_tasks_for_day(u.user_id, local_date)
                if tasks:
                    text = "🔔 Задачи на сегодня:\n" + "\n".join(
                        f"- {t.description}" for t in tasks
                    )
                    await bot.send_message(u.user_id, text)

            # ========= 2. НАПОМИНАНИЯ ПО ЗАДАЧАМ =========

            remind_tasks = TaskRepository.get_tasks_to_remind(u.user_id)

            for task in remind_tasks:
                remind_at = (
                    task.remind_time
                    if task.remind_time
                    else u.notify_time
                )
                remind_day=(
                    task.remind_date
                    if task.remind_date
                    else local_date
                )

                if (
                    remind_at.hour == local_time.hour and
                    remind_at.minute == local_time.minute and
                    remind_day==local_date
                ):
                    await bot.send_message(
                        u.user_id,
                        f"⏰ Напоминание:\n{task.description}"
                    )


        await asyncio.sleep(60)
