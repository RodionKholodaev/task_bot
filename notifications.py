import asyncio
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from config import BOT_TOKEN
from database import get_session, get_tasks_today, get_all_tasks, get_tasks_with_reminders
from models import UserSettings, Task

bot = Bot(token=BOT_TOKEN)


async def notification_loop():
    while True:
        now_utc = datetime.utcnow()

        s = get_session()
        try:
            users = s.query(UserSettings).all()
        finally:
            s.close()

        for u in users:
            local_now = now_utc + timedelta(hours=u.utc_offset)
            local_date = local_now.date()
            local_time = local_now.time().replace(second=0, microsecond=0)

            # ========= 1. ЕЖЕДНЕВНОЕ УВЕДОМЛЕНИЕ =========
            if (
                local_time.hour == u.notify_time.hour and
                local_time.minute == u.notify_time.minute
            ):
                tasks = get_tasks_today(u.user_id, local_date)
                if tasks:
                    text = "🔔 Задачи на сегодня:\n" + "\n".join(
                        f"- {t.description}" for t in tasks
                    )
                    await bot.send_message(u.user_id, text)

            # ========= 2. НАПОМИНАНИЯ ПО ЗАДАЧАМ =========
            s = get_session()
            try:
                remind_tasks = s.query(Task).filter(
                    Task.user_id == u.user_id,
                    Task.is_completed == False,
                    Task.remind_date.isnot(None)  # Напоминание установлено
                ).all()

                for task in remind_tasks:
                    remind_at = (
                        task.remind_time
                        if task.remind_time
                        else u.notify_time
                    )

                    if (
                        remind_at.hour == local_time.hour and
                        remind_at.minute == local_time.minute
                    ):
                        await bot.send_message(
                            u.user_id,
                            f"⏰ Напоминание:\n{task.description}"
                        )
                        task.reminded = True

                s.commit()
            finally:
                s.close()

        await asyncio.sleep(60)
