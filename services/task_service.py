from database import get_user_settings, get_tasks_for_day, get_tasks_week, get_all_tasks
from datetime import datetime, timedelta

class TaskService:
    @staticmethod
    def get_day_tasks(user_id: int, day_shift: int):

        settings = get_user_settings(user_id)
        offset = settings.utc_offset if settings else 0

        target_date = (
            datetime.utcnow() + timedelta(days=day_shift, hours=offset)
        ).date()

        return get_tasks_for_day(user_id, target_date)

    @staticmethod
    def get_week_task(user_id: int):
        settings = get_user_settings(user_id)
        offset = settings.utc_offset if settings else 0

        start = (datetime.utcnow() + timedelta(hours=offset)).date()
        end = start + timedelta(days=7)

        tasks = get_tasks_week(user_id, start, end)
        return tasks
    
    @staticmethod
    def get_all_tasks(user_id: int):
        tasks = get_all_tasks(user_id)
        return tasks