from sqlalchemy import select, func, and_, extract, case
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, date
from typing import Dict, List, Any

from models import Task, ShoppingItem, UserSettings  # Замените на ваши пути импорта
# не проверял код!
class StatisticRepository:
    
    @staticmethod
    async def get_user_stats(session: AsyncSession, user_id: int) -> Dict[str, Any]:
        # 1. Получаем настройки пользователя (смещение UTC)
        settings_query = await session.execute(
            select(UserSettings.utc_offset).where(UserSettings.user_id == user_id)
        )
        utc_offset = settings_query.scalar() or 0
        
        # Вычисляем локальное время пользователя
        user_now = datetime.utcnow() + timedelta(hours=utc_offset)
        today_date = user_now.date()
        
        # 2. Общая статистика задач (выполнено/нет)
        tasks_status_query = await session.execute(
            select(
                func.count(case((Task.is_completed == True, 1))),
                func.count(case((Task.is_completed == False, 1)))
            ).where(Task.user_id == user_id)
        )
        completed_tasks, uncompleted_tasks = tasks_status_query.tuples().first() #type: ignore

        # 3. Задачи по категориям сложности (только невыполненные)
        complexity_query = await session.execute(
            select(Task.category, func.count(Task.id))
            .where(and_(Task.user_id == user_id, Task.is_completed == False))
            .group_by(Task.category)
        )
        complexity_stats = dict(complexity_query.tuples().all())

        # 4. Задачи на неделю (с сегодня до воскресенья)
        # Определяем сколько дней осталось до конца недели (воскресенье = 6)
        current_weekday = today_date.weekday()
        days_until_sunday = 6 - current_weekday
        end_of_week = today_date + timedelta(days=days_until_sunday)

        weekly_query = await session.execute(
            select(Task.deadline_day, func.count(Task.id))
            .where(and_(
                Task.user_id == user_id,
                Task.deadline_day >= today_date,
                Task.deadline_day <= end_of_week,
                Task.is_completed == False
            ))
            .group_by(Task.deadline_day)
        )
        weekly_tasks_raw = dict(weekly_query.tuples().all())
        
        # Формируем список по дням (даже если там 0 задач)
        weekly_schedule = []
        days_map = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i in range(days_until_sunday + 1):
            target_date = today_date + timedelta(days=i)
            count = weekly_tasks_raw.get(target_date, 0)
            weekly_schedule.append({
                "day_name": days_map[target_date.weekday()],
                "count": count
            })

        # 5. Покупки по категориям (не купленные, где > 0)
        shopping_query = await session.execute(
            select(ShoppingItem.category, func.count(ShoppingItem.id))
            .where(and_(ShoppingItem.user_id == user_id, ShoppingItem.is_bought == False))
            .group_by(ShoppingItem.category)
            .having(func.count(ShoppingItem.id) > 0)
        )
        shopping_stats = shopping_query.tuples().all()

        return {
            "completed": completed_tasks,
            "uncompleted": uncompleted_tasks,
            "complexity": complexity_stats,
            "weekly": weekly_schedule,
            "shopping": shopping_stats
        }