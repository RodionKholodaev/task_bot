import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from config import BOT_TOKEN
from database import get_session, get_tasks_today
from models import UserSettings

bot = Bot(token=BOT_TOKEN)


async def notification_loop():
    """Отправка уведомлений о задачах на сегодня"""
    while True:
        now = datetime.utcnow()

        s = get_session()
        try:
            users = s.query(UserSettings).all()
        finally:
            s.close()

        for u in users:
            local = now + timedelta(hours=u.utc_offset)
            if (
                local.hour == u.notify_time.hour and
                local.minute == u.notify_time.minute
            ):
                tasks = get_tasks_today(u.user_id, local.date())
                if tasks:
                    text = "🔔 Задачи на сегодня:\n" + "\n".join(
                        f"- {t.description}" for t in tasks
                    )
                    await bot.send_message(u.user_id, text)

        await asyncio.sleep(60)
