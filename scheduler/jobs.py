from datetime import datetime, timedelta
from typing import Optional
import logging

from aiogram import Bot
from config import BOT_TOKEN
from db.task_repository import TaskRepository

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN) #type: ignore


async def send_daily_notification(user_id: int, utc_offset: int):
    """
    Ежедневное уведомление о задачах на день.
    Вызывается в notify_time пользователя.
    """
    try:
        logger.info(f"Ежедневное уведомление для пользователя {user_id}")
        
        # Получаем текущую дату в часовом поясе пользователя
        now_utc = datetime.utcnow()
        local_now = now_utc + timedelta(hours=utc_offset)
        local_date = local_now.date()
        
        # Получаем задачи на сегодня с deadline_day
        tasks = await TaskRepository.get_tasks_with_deadline(user_id, local_date)
        
        if tasks:
            text = "🔔 Задачи на сегодня:\n" + "\n".join(
                f"- {t.description}" for t in tasks
            )
            await bot.send_message(user_id, text)
            logger.info(f"Отправлено ежедневное уведомление пользователю {user_id}")
        else:
            logger.info(f"Нет задач на сегодня для пользователя {user_id}")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке ежедневного уведомления: {e}")


async def send_task_reminder(user_id: int, task_id: int):
    """
    Напоминание о конкретной задаче.
    Вызывается в remind_date/remind_time задачи.
    """
    try:
        logger.info(f"Напоминание о задаче {task_id} для пользователя {user_id}")
        
        task = await TaskRepository.get_task_by_id(task_id)
        
        if task and not task.is_completed: #type: ignore
            text = f"⏰ Напоминание:\n{task.description}"
            await bot.send_message(user_id, text)
            logger.info(f"Отправлено напоминание о задаче {task_id}")
        else:
            logger.info(f"Задача {task_id} не найдена или выполнена")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания о задаче: {e}")