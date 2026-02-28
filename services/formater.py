from models import Task, ShoppingItem
from keyboards import READABLE_CATEGORIES
class Formater:
    @staticmethod
    def format_task(task: Task, make_task: bool) -> str:

        cat_text = READABLE_CATEGORIES.get(task.category, task.category)
        date_text = task.deadline_day.strftime("%d-%m-%Y") if task.deadline_day else None
        time = task.deadline_time.strftime("%H:%M") if task.deadline_time else None
        remind_date_str=task.remind_date.strftime("%d-%m-%Y") if task.remind_date else None
        remind_time = task.remind_time.strftime("%H:%M") if task.remind_time else None

        status = "добавлена" if make_task else "обновлена"
        response_text = (
            f"✅ **Задача {status}!**\n\n"
            f"📝 **Что:** {task.description}\n"
            f"📁 **Категория:** {cat_text}\n"
            f"📅 **Дата:** {date_text}\n"
            f"⏰ **Время:** {time}\n"
            f"🚨 **Напоминание дата:** {remind_date_str}\n"
            f"⏱️ **Напоминание время:** {remind_time}\n"
            f"🆔 ID задачи: {task.id}"
        )

        return response_text
    


