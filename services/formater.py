from models import Task, ShoppingItem
from keyboards import READABLE_CATEGORIES
class Formater:
    """
    Создает ответ пользователю при создании/редактировании задачи/покупки
    Создает ответ пользователю при выводе покупки (а где задача?)
    """
    @staticmethod
    def format_task(task: Task, make_task: bool) -> str:

        cat_text = READABLE_CATEGORIES.get(task.category, task.category)
        date_text = task.deadline_day.strftime("%d-%m-%Y") if task.deadline_day else 'Нет'
        time = task.deadline_time.strftime("%H:%M") if task.deadline_time else 'Нет'
        remind_date_str=task.remind_date.strftime("%d-%m-%Y") if task.remind_date else 'Нет'
        remind_time = task.remind_time.strftime("%H:%M") if task.remind_time else 'Нет'

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
    
    @staticmethod
    def format_shopping_list(item: ShoppingItem) -> str:

        # предварительная подготовка данных (чтобы не было 1.0 там, где не нужно)
        amount_val = int(item.amount) if item.amount and item.amount.is_integer() else item.amount
        quantity_text = f"{amount_val} {item.unit}" if item.amount else "Не указано"

        # словарь для красивого отображения категорий (опционально)
        categories_map = {
            "grocery": "Продукты",
            "pharmacy": "Лекарства",
            "household": "Для дома",
            "beauty": "Гигиена",
            "electronics": "Техника",
            "clothes": "Одежда",
            "other": "Другое"
        }
        cat_display = categories_map.get(item.category, item.category or "Не указана")

        response_text = (
            f"🛒 **Товар добавлен в список!**\n\n"
            f"📦 **Что:** {item.item}\n"
            f"🔢 **Кол-во:** {quantity_text}\n"
            f"📁 **Категория:** {cat_display}\n"
            f"✅ **Статус:** {'Куплено' if item.is_bought else 'В списке'}\n\n"
            f"🆔 ID товара: {item.id}"
        )
        
        return response_text
    
    

    @staticmethod
    def format_category_item(item: ShoppingItem) -> str:

        amount_val = int(item.amount) if item.amount and item.amount.is_integer() else item.amount
        quantity_text = f"{amount_val} {item.unit}" if item.amount else ""

        response_text = (
            f"*{item.item} {quantity_text}*\n"
            f"ID товара: {item.id}"
        )
        return response_text
