from db.user_repository import UserRepository
from db.task_repository import TaskRepository
from datetime import datetime, timedelta
from keyboards import TASK_CATEGORY_MAP
from sqlalchemy.ext.asyncio import AsyncSession

import logging
logger = logging.getLogger(__name__)

class TaskService:
    @staticmethod
    async def get_day_tasks(s: AsyncSession, user_id: int, day_shift: int):
        logger.info("получаем задачи на день")
        settings = await UserRepository.get_user_settings(s, user_id)
        offset = settings.utc_offset if settings else 0 

        target_date = (
            datetime.utcnow() + timedelta(days=day_shift, hours=offset) # type: ignore 
        ).date()

        return await TaskRepository.get_tasks_for_day(s, user_id, target_date)

    @staticmethod
    async def get_week_task(s: AsyncSession, user_id: int):
        logger.info("получаем задачи на неделю")
        settings = await UserRepository.get_user_settings(s, user_id)
        offset = settings.utc_offset if settings else 0

        start = (datetime.utcnow() + timedelta(hours=offset)).date() # type: ignore 
        end = start + timedelta(days=7)

        tasks = await TaskRepository.get_tasks_week(s, user_id, start, end)
        return tasks
    
    @staticmethod
    async def get_all_tasks(s: AsyncSession, user_id: int):
        logger.info("получаем все задачи")
        tasks = await TaskRepository.get_all_tasks(s, user_id)
        return tasks
    
    @staticmethod
    async def get_category_task(s: AsyncSession, user_id: int, category: str):
        logger.info("получаем задачи по категории")
        category = TASK_CATEGORY_MAP[category]
        tasks = await TaskRepository.get_tasks_by_category(s, user_id, category)
        
        return tasks