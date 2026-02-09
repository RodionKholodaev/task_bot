from datetime import datetime, timedelta, timezone
from models import Task
from database import save_task, save_new_message_id
from keyboards import task_inline, READABLE_CATEGORIES
from ai_client import classify_task, edit_task
from handlers.commands import get_user_settings, get_task_by_message_id

class TaskService:
    @staticmethod
    def get_user_time(user_id):
        """Получает настройки пользователя и текущее время в его часовом поясе."""
        settings = get_user_settings(user_id)
        if not settings:
            return None, {"error": "Не найден часовой пояс пользователя"}

        user_tz = timezone(timedelta(hours=settings.utc_offset))
        user_datetime = datetime.now(user_tz)
        return user_datetime, None

    @staticmethod
    async def classify_task_with_ai(user_datetime, message_text):
        """Классифицирует задачу с помощью нейросети."""
        dt_string = user_datetime.strftime("%Y-%m-%d %H:%M")

        if len(message_text) > 500:
            return {"error": "Слишком длинный текст"}

        data_message = await classify_task(f"сегодня {dt_string}, {message_text}")

        if isinstance(data_message, str):
            return {"error": f"Ошибка с нейросетью: {data_message}"}

        return data_message
    
    # TODO НУЖНО ДОПИСАТЬ ЭТО И ПОСМОТРЕТЬ ЧТО ТАМ С ВЫЗОВАМИ, ВОЗМОЖНО ОШИБКА
    @staticmethod
    async def edit_task_with_ai(message_text):
        """Радактирует задачу с помощью нейросети."""
        # {
        # "request":"изменения от пользователя"
        # "category": "тип категории",
        # "date": "дата выполнения задачи в формате YYYY-MM-DD или пустая строка",
        # "time": "время выполнения в формате HH:MM или пустая строка",
        # "remind_date": "дата напоминания в формате YYYY-MM-DD или пустая строка",
        # "remind_time": "время напоминания в формате HH:MM или пустая строка",
        # "task": "краткое описание задачи"
        # }
        if len(message_text) > 500:
            return {"error": "Слишком длинный текст"}

        data_message = await edit_task()

        if isinstance(data_message, str):
            return {"error": f"Ошибка с нейросетью: {data_message}"}

        return data_message

    @staticmethod
    def create_task_objects(user_id, message_text, data_list, edit):
        """Создает задачи на основе данных от нейросети."""
        tasks = []

        for data in data_list:
            try:
                deadline_day = datetime.strptime(data["date"], "%Y-%m-%d").date() if data.get("date") else None
            except (ValueError, TypeError):
                deadline_day = None

            try:
                time_str = data.get("time")
                deadline_time = datetime.strptime(time_str, "%H:%M").time() if time_str else None
            except (ValueError, TypeError):
                deadline_time = None

            try:
                remind_date_str = data.get("remind_date")
                remind_date = datetime.strptime(remind_date_str, "%Y-%m-%d").date() if remind_date_str else None
            except Exception:
                remind_date = None

            try:
                remind_time_str = data.get("remind_time")
                remind_time = datetime.strptime(remind_time_str, "%H:%M").time() if remind_time_str else None
            except Exception:
                remind_time = None

            task = Task(
                user_id=user_id,
                description=data.get("task", message_text),
                category=data.get("category", "short_30"),
                deadline_day=deadline_day,
                deadline_time=deadline_time,
                remind_time=remind_time,
                remind_date=remind_date
            )

            save_task(task)

            cat_text = READABLE_CATEGORIES.get(task.category, task.category)
            date_text = task.deadline_day.strftime("%d-%m-%Y") if task.deadline_day else None
            time = task.deadline_time.strftime("%H:%M") if task.deadline_time else None
            remind_date_str = task.remind_date.strftime("%d-%m-%Y") if task.remind_date else None
            remind_time = task.remind_time.strftime("%H:%M") if task.remind_time else None

            response_text = (
                f"✅ **Задача {'изменена' if edit else 'добавлена'}!**\n\n"
                f"📝 **Что:** {task.description}\n"
                f"📁 **Категория:** {cat_text}\n"
                f"📅 **Дата:** {date_text}\n"
                f"⏰ **Время:** {time}\n"
                f"🚨 **Напоминание дата:** {remind_date_str}\n"
                f"⏱️ **Напоминание время:** {remind_time}"
            )

            tasks.append({"task": task, "response_text": response_text})

        return tasks

    @staticmethod
    async def process_task(user_id, message_text, edit: bool):
        """Основной метод для обработки задачи."""
        user_datetime, error = TaskService.get_user_time(user_id)
        if error:
            return error

        if edit:
            data_message = await TaskService.classify_task_with_ai(user_datetime, message_text)
            if "error" in data_message:
                return data_message
        else:
            data_message = await TaskService.edit_task_with_ai() # что вставить?
            if "error" in data_message:
                return data_message

        if data_message.get("type") == "chat":
            return {"chat_message": data_message.get("message")}

        tasks = TaskService.create_task_objects(user_id, message_text, data_message.get("items"), edit)
        return {"tasks": tasks}
