from datetime import datetime, timedelta, time, date
from typing import Optional
import logging

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from .scheduler_config import scheduler
from .jobs import send_daily_notification, send_task_reminder
from db.user_repository import UserRepository
from db.task_repository import TaskRepository

logger = logging.getLogger(__name__)


def _get_user_notify_time(user_id: int) -> Optional[dict]:
    """Получить notify_time и utc_offset пользователя"""
    user = UserRepository.get_user_settings(user_id)
    if user and user.notify_time: #type: ignore
        return {
            'hour': user.notify_time.hour,
            'minute': user.notify_time.minute,
            'utc_offset': user.utc_offset
        }
    return None


def create_daily_notification_job(user_id: int, utc_offset: int, 
                                   notify_hour: int, notify_minute: int):
    """
    Создать cron-джобу для ежедневного уведомления.
    Время указывается в локальном времени пользователя.
    """
    job_id = f"daily_{user_id}"
    
    # Корректируем время на UTC
    utc_hour = (notify_hour - utc_offset) % 24
    
    trigger = CronTrigger(
        hour=utc_hour,
        minute=notify_minute,
        second=0,
        timezone='UTC'
    )
    
    scheduler.add_job(
        func=send_daily_notification,
        trigger=trigger,
        args=[user_id, utc_offset],
        id=job_id,
        name=f"Daily notification for user {user_id}",
        replace_existing=True,
        jobstore='default'
    )
    
    logger.info(f"Создана daily-джоба {job_id} на {utc_hour}:{notify_minute} по UTC")


def create_task_reminder_job(user_id: int, task_id: int,
                              remind_date: date,
                              remind_time: Optional[time],
                              notify_time: time,
                              utc_offset: int):
    """
    Создать date-джобу для напоминания о задаче.
    
    Args:
        user_id: ID пользователя
        task_id: ID задачи
        remind_date: Дата напоминания (локальная)
        remind_time: Время напоминания (локальное), если None - используется notify_time
        notify_time: Время уведомления пользователя по умолчанию
        utc_offset: Часовой пояс пользователя
    """
    job_id = f"reminder_{task_id}"
    
    # Определяем время напоминания: если есть remind_time - используем его, иначе notify_time
    final_time = remind_time if remind_time is not None else notify_time
    
    # Создаём datetime в локальном времени пользователя
    remind_local = datetime.combine(remind_date, final_time)
    
    # Конвертируем локальное время в UTC
    remind_utc = remind_local - timedelta(hours=utc_offset)
    
    # Не создаём джобы в прошлом
    now_utc = datetime.utcnow()
    if remind_utc <= now_utc:
        logger.warning(f"Время напоминания {remind_utc} в прошлом для задачи {task_id}")
        return
    
    trigger = DateTrigger(run_date=remind_utc, timezone='UTC')
    
    scheduler.add_job(
        func=send_task_reminder,
        trigger=trigger,
        args=[user_id, task_id],
        id=job_id,
        name=f"Reminder for task {task_id}",
        replace_existing=True,
        jobstore='default'
    )
    
    logger.info(f"Создана reminder-джоба {job_id} на {remind_utc} UTC (локальное: {remind_local})")


def remove_daily_notification_job(user_id: int):
    """Удалить daily-джобу пользователя"""
    job_id = f"daily_{user_id}"
    try:
        scheduler.remove_job(job_id, jobstore='default')
        logger.info(f"Удалена daily-джоба {job_id}")
    except Exception as e:
        logger.warning(f"Не удалось удалить daily-джобу {job_id}: {e}")


def remove_task_reminder_job(task_id: int):
    """Удалить reminder-джобу задачи"""
    job_id = f"reminder_{task_id}"
    try:
        scheduler.remove_job(job_id, jobstore='default')
        logger.info(f"Удалена reminder-джоба {job_id}")
    except Exception as e:
        logger.warning(f"Не удалось удалить reminder-джобу {task_id}: {e}")


def load_all_jobs_from_db():
    """
    Загрузить все джобы из БД при старте бота.
    Вызывается один раз при инициализации.
    """
    logger.info("Загрузка джобов из БД...")
    
    users = UserRepository.get_all_users()
    if not users:
        logger.info("Нет пользователей для загрузки джобов")
        return
    
    for user in users:
        if not user.notify_time: #type: ignore
            continue
            
        # Создаём daily-джобу для каждого пользователя
        create_daily_notification_job(
            user_id=user.user_id, #type: ignore
            utc_offset=user.utc_offset, #type: ignore
            notify_hour=user.notify_time.hour,
            notify_minute=user.notify_time.minute
        )
        
        # Создаём reminder-джобы для всех активных задач с remind_date
        tasks = TaskRepository.get_tasks_with_reminder(user.user_id) #type: ignore
        for task in tasks:
            if task.remind_date and not task.is_completed: #type: ignore
                create_task_reminder_job(
                    user_id=user.user_id, #type: ignore
                    task_id=task.id, #type: ignore
                    remind_date=task.remind_date, #type: ignore
                    remind_time=task.remind_time, #type: ignore
                    notify_time=user.notify_time, #type: ignore
                    utc_offset=user.utc_offset #type: ignore
                )
    
    logger.info(f"Загружено джобов: {len(scheduler.get_jobs())}")