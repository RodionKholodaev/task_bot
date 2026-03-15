from datetime import date
from typing import Sequence
from sqlalchemy import select
from models import Task
from sqlalchemy.ext.asyncio import AsyncSession
from payments_repository import PaymentsRepository
class TaskRepository:

    @staticmethod
    async def save_task(s: AsyncSession, task: Task) -> Task:
        """Сохранение задачи"""

        async with s.begin():
            s.add(task)
        await s.refresh(task)
        return task

    @staticmethod
    async def get_tasks_for_day(s: AsyncSession, user_id: int, day: date) -> Sequence[Task]:
        """Получение задач на указанный день"""

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.deadline_day == day)
            .where(Task.is_completed == False)
            .order_by(Task.deadline_time)
        )
        return result.scalars().all()

    @staticmethod
    async def get_tasks_week(s: AsyncSession, user_id: int, start: date, end: date) -> Sequence[Task]:
        """Получение задач на неделю"""

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.deadline_day >= start)
            .where(Task.deadline_day <= end)
            .where(Task.is_completed == False)
            .order_by(Task.deadline_day)
        )
        return result.scalars().all()

    @staticmethod
    async def get_tasks_to_remind(s: AsyncSession, user_id: int) -> Sequence[Task]:

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.is_completed == False)
            .where(Task.remind_date.isnot(None))
        )
        return result.scalars().all()

    @staticmethod
    async def get_tasks_by_category(s: AsyncSession, user_id: int, category: str) -> Sequence[Task]:

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.category == category)
            .where(Task.is_completed == False)
        )
        return result.scalars().all()


    @staticmethod
    async def get_tasks_with_deadline(s: AsyncSession, user_id: int, deadline_date: date) -> Sequence[Task]:
        """Получить задачи с deadline на указанную дату"""

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.deadline_day == deadline_date)
            .where(Task.is_completed == False)
        )
        return result.scalars().all()


    @staticmethod
    async def get_tasks_with_reminder(s: AsyncSession, user_id: int) -> Sequence[Task]:
        """Получить все задачи с remind_date для пользователя"""

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.remind_date != None)
            .where(Task.is_completed == False)
        )
        return result.scalars().all()

    @staticmethod
    async def get_task_by_id(s: AsyncSession, task_id: int) -> Task | None:
        """получение задачи по ее id"""

        result = await s.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_tasks(s: AsyncSession, user_id: int) -> Sequence[Task]:
        """Получение всех задач пользователя"""

        result = await s.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.is_completed == False)
        )
        return result.scalars().all()

    @staticmethod
    async def mark_done(s: AsyncSession, task_id: int, user_id: int) -> bool:
        """Пометить задачу выполненной"""
        await PaymentsRepository.update_user_counter(s, user_id, field="tasks", delta=-1)

        result = await s.execute(
            select(Task)
            .where(Task.id == task_id)
            .where(Task.user_id == user_id)
        )
        task = result.scalars().first()
        if not task:
            return False
        task.is_completed = True  # type: ignore
        await s.commit()
        return True

    @staticmethod
    async def delete_task(s: AsyncSession, task_id: int, user_id: int) -> bool:
        """Удалить задачу"""
        await PaymentsRepository.update_user_counter(s, user_id, field="tasks", delta=-1)

        result = await s.execute(
            select(Task)
            .where(Task.id == task_id)
            .where(Task.user_id == user_id)
        )
        task = result.scalars().first()
        if not task:
            return False
        await s.delete(task)
        await s.commit()
        return True

