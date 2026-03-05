from models import Task, ShoppingItem
from keyboards import READABLE_CATEGORIES
from database import get_user_settings, get_task_by_id, get_item_by_id
from datetime import datetime, timedelta, timezone

import logging 
logger = logging.getLogger(__name__)

class Formater:
    """
    (формирует сообщения для отдачи и получения)
    Создает ответ пользователю при создании/редактировании задачи/покупки
    Создает ответ пользователю при выводе покупки/задачи
    Создает запрос от пользователя при редактировании
    """

    @staticmethod
    def make_description(id: int, type: str, dt_string: str, request: str) -> str | None:
        """
        запрос пользователя для редактирования задачи
        id - id объекта
        type - тип объекта (задача/продукт)
        dt_string - день, дата, время
        request - что пользователю нужно
        """

        if type == "tasks":
            logger.info("создаю запрос пользователя в LLM для задачи")
            task = get_task_by_id(id)
            if not task:
                return None
            description = f'''
            Сегодня {dt_string}. Вот моя задача:
            {{
            "type": "tasks",
            "items": [
                {{
                "category": "{task.category}",
                "date": "{task.deadline_day}",
                "time": "{task.deadline_time}",
                "remind_date": "{task.remind_date}",
                "remind_time": "{task.remind_time}",
                "task": "{task.description}"
                }}
            ]
            }}
            Вот моя просьба: {request}
            '''
            logger.debug(f"итоговый текст: {description}")
            return description
        elif type == "shopping_list":
            logger.info("создаю запрос пользователя в LLM для покупки")
            item = get_item_by_id(id)
            if not item:
                return None
            
            description = f'''
            Сегодня {dt_string}. Вот моя покупка:
            {{
            "type": "shopping_list",
            "items": [
                {{
                "category": {item.category},
                "item": {item.item},
                "amount": {item.amount},
                "unit": {item.unit}
                }}
            ]
            }}
            Вот моя просьба: {request}
            '''
            logger.debug(f"итоговый текст: {description}")
            return description
        else:
            logger.error("Неизвестный тип объекта")
            return None

    @staticmethod
    def get_user_time(user_id: int) -> str | None:
        logger.info("получаем день, дату и время для LLM")
        WEEKDAYS_RU = {
            0: "Понедельник",
            1: "Вторник",
            2: "Среда",
            3: "Четверг",
            4: "Пятница",
            5: "Суббота",
            6: "Воскресенье",
        }

        settings = get_user_settings(user_id)
        if not settings:
            return None

        # Часовой пояс пользователя
        user_tz = timezone(timedelta(hours=settings.utc_offset))
        user_datetime = datetime.now(user_tz)

        # День недели
        weekday_ru = WEEKDAYS_RU[user_datetime.weekday()]
        weekday_en = user_datetime.strftime("%A")

        # Итоговая строка
        dt_string = f"{weekday_ru} ({weekday_en}), {user_datetime.strftime('%Y-%m-%d %H:%M')}"

        logger.debug(f"итоговый текст: {dt_string}")
        return dt_string

    @staticmethod
    def format_task(task: Task, make_task: bool) -> str:

        logger.info("формирую сообщение о создании/редактировании задачи")

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

        logger.info("формирую сообщение о создании/редактировании покупки")

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
        logger.info("определяю что хочет изменить пользователь")
        amount_val = int(item.amount) if item.amount and item.amount.is_integer() else item.amount
        quantity_text = f"{amount_val} {item.unit}" if item.amount else ""

        response_text = (
            f"*{item.item} {quantity_text}*\n"
            f"ID товара: {item.id}"
        )
        logger.debug(f"пользователь хочет изменить: {response_text}")
        return response_text
    
    @staticmethod
    def format_short_task(task: Task, is_day: bool) -> str:
        if is_day:
            deadline_time = (
                task.deadline_time.strftime('%H:%M')
                if task.deadline_time else ""
            )

            answer = (
                f"{deadline_time} {task.description}\n"
                f"ID задачи: {task.id}"
            )
        else:
            deadline_day = task.deadline_day.strftime('%d-%m-%Y') if task.deadline_day else ''
            deadline_time = task.deadline_time.strftime('%H-%M') if task.deadline_time else ''

            answer = (
                f" {deadline_day} {deadline_time} {task.description}\n"
                f"ID задачи: {task.id}"
                )
        return answer
