from datetime import date
from typing import List
from models import  Task
from db.database import get_session

class TaskRepository:
    
    @staticmethod
    def save_task(task: Task) -> Task:
        """Сохранение задачи"""
        s = get_session()
        try:
            s.add(task)
            s.commit()
            s.refresh(task)
            return task
        finally:
            s.close()

    @staticmethod
    def get_tasks_for_day(user_id: int, day: date) -> List[Task]:
        """Получение задач на указаный день"""
        s = get_session()
        try:
            return s.query(Task).filter(
                Task.user_id == user_id,
                Task.deadline_day == day,
                Task.is_completed == False
            ).order_by(Task.deadline_time).all()
        finally:
            s.close()

    @staticmethod
    def get_tasks_week(user_id: int, start: date, end: date) -> List[Task]:
        """Получение задач на неделю"""
        s = get_session()
        try:
            return s.query(Task).filter(
                Task.user_id == user_id,
                Task.deadline_day >= start,
                Task.deadline_day <= end,
                Task.is_completed == False
            ).order_by(Task.deadline_day).all()
        finally:
            s.close()

    @staticmethod
    def get_tasks_to_remind(user_id: int) -> List[Task]:
        s = get_session()
        try:
            return s.query(Task).filter(
                        Task.user_id == user_id,
                        Task.is_completed == False,
                        Task.remind_date.isnot(None)  # Напоминание установлено
                    ).all()
        finally:
            s.close()

    @staticmethod
    def get_tasks_by_category(user_id: int, category: str) -> List[Task]:
        s = get_session()
        try:
            return s.query(Task).filter(
                Task.user_id == user_id,
                Task.category == category,
                Task.is_completed == False
            ).all()
        finally:
            s.close()


    @staticmethod
    def get_task_by_id(task_id: int) -> Task:
        """получение задачи по ее id"""
        s = get_session()
        try:
            return s.query(Task).filter(Task.id==task_id).first()
        finally:
            s.close()
    @staticmethod
    def get_all_tasks(user_id: int) -> List[Task]:
        """Получение всех задач пользователя"""
        s = get_session()
        try:
            return s.query(Task).filter(Task.user_id == user_id, Task.is_completed==False).all()
        finally:
            s.close()

    @staticmethod
    def mark_done(task_id: int, user_id: int) -> bool:
        """Пометить задачу выполненой"""
        s = get_session()
        try:
            task = s.query(Task).filter_by(id=task_id, user_id=user_id).first()
            if not task:
                return False
            task.is_completed = True
            s.commit()
            return True
        finally:
            s.close()



    @staticmethod
    def delete_task(task_id: int, user_id: int) -> bool:
        """Удалить задачу"""
        s = get_session()
        try:
            task = s.query(Task).filter_by(id=task_id, user_id=user_id).first()
            if not task:
                return False
            s.delete(task)
            s.commit()
            return True
        finally:
            s.close()

