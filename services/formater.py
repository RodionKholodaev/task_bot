from models import Task, ShoppingItem
from keyboards import READABLE_CATEGORIES
from db.user_repository import UserRepository
from db.task_repository import TaskRepository
from db.shopping_repository import ShoppingRepository
from datetime import datetime, timedelta, timezone
from models import SubscriptionTypes
from sqlalchemy.ext.asyncio import AsyncSession
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
    async def make_description(s: AsyncSession, id: int, type: str, request: str) -> str | None:
        """
        запрос пользователя для редактирования задачи
        id - id объекта
        type - тип объекта (задача/продукт)
        dt_string - день, дата, время
        request - что пользователю нужно
        """

        if type == "tasks":

            task = await TaskRepository.get_task_by_id(s, id)
            if not task:
                return None
            description = f'''
            Вот моя задача:
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
            logger.debug(f"итоговый текст:\n {description}")
            return description
        elif type == "shopping_list":
            logger.info("создаю запрос пользователя в LLM для покупки")
            item = await ShoppingRepository.get_item_by_id(s, id)
            if not item:
                return None
            
            description = f'''
            Вот моя покупка:
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
    async def get_week_info(s: AsyncSession, user_id: int, start_date=None):
        """
        Возвращает строку с информацией о текущем дне и следующих 7 днях.
        
        Args:
            start_date: Дата, от которой ведется отсчет (по умолчанию - сегодня)
        
        Returns:
            Строка с информацией о днях недели в формате:
            "Сегодня 13.03.2026 - пятница, завтра 14.03.2026 - суббота, ..."
        """
        # Если дата не указана, используем сегодня
        if start_date is None:
            settings = await UserRepository.get_user_settings(s, user_id)
            if not settings:
                return None
            elif settings.notify_time is None and settings.utc_offset is None:
                return None

            # Часовой пояс пользователя
            user_tz = timezone(timedelta(hours=settings.utc_offset)) # type: ignore 
            start_date = datetime.now(user_tz)
        

        
        # Словарь для перевода дней недели на русский
        weekdays_ru = {
            0: 'понедельник',
            1: 'вторник', 
            2: 'среда',
            3: 'четверг',
            4: 'пятница',
            5: 'суббота',
            6: 'воскресенье'
        }
        
        # Формируем результат
        result_parts = []
        
        # Сегодня
        current_date = start_date
        weekday_num = current_date.weekday()  # 0 - понедельник, 6 - воскресенье
        date_str = current_date.strftime("%d.%m.%Y")
        result_parts.append(f"Сегодня {date_str} - {weekdays_ru[weekday_num]}")
        
        # Следующие 7 дней
        days_offset = ["завтра", "через 2 дня", "через 3 дня", "через 4 дня", 
                    "через 5 дней", "через 6 дней", "через 7 дней"]
        
        for i, offset_text in enumerate(days_offset, 1):
            next_date = start_date + timedelta(days=i)
            weekday_num = next_date.weekday()
            date_str = next_date.strftime("%d.%m.%Y")
            result_parts.append(f"{offset_text} {date_str} - {weekdays_ru[weekday_num]}")
        
        # Объединяем все части через запятую с пробелом
        return ", ".join(result_parts)


    @staticmethod
    async def get_user_time(s: AsyncSession, user_id: int) -> str | None:
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

        settings = await UserRepository.get_user_settings(s, user_id)
        if not settings:
            return None
        elif settings.notify_time is None and settings.utc_offset is None:
            return None

        # Часовой пояс пользователя
        user_tz = timezone(timedelta(hours=settings.utc_offset)) # type: ignore 
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

        cat_text = READABLE_CATEGORIES.get(task.category) # type: ignore 
        date_text = task.deadline_day.strftime("%d-%m-%Y") if task.deadline_day else 'Нет' # type: ignore 
        time = task.deadline_time.strftime("%H:%M") if task.deadline_time else 'Нет' # type: ignore 
        remind_date_str=task.remind_date.strftime("%d-%m-%Y") if task.remind_date else 'Нет' # type: ignore 
        remind_time = task.remind_time.strftime("%H:%M") if task.remind_time else 'Нет' # type: ignore 

        status = "добавлена" if make_task else "обновлена"
        response_text = (
            f"✅ **Задача {status}!**\n\n"
            f"📝 **Что:** {task.description}\n"
            f"📁 **Категория:** {cat_text}\n"
            f"📅 **Дата:** {date_text}\n"
            f"⏰ **Время:** {time}\n"
            f"🚨 **Дата напоминания:** {remind_date_str}\n"
            f"⏱️ **Время напоминания:** {remind_time}\n"
            f"🆔 ID задачи: {task.id}"
        )

        return response_text
    
    @staticmethod
    def format_shopping_list(item: ShoppingItem) -> str:

        logger.info("формирую сообщение о создании/редактировании покупки")

        # предварительная подготовка данных (чтобы не было 1.0 там, где не нужно)
        amount_val = int(item.amount) if item.amount and item.amount.is_integer() else item.amount # type: ignore 
        quantity_text = f"{amount_val} {item.unit}" if item.amount else "Не указано" # type: ignore

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
        cat_display = categories_map.get(item.category, item.category or "Не указана") # type: ignore 

        response_text = (
            f"🛒 **Товар добавлен в список!**\n\n"
            f"📦 **Что:** {item.item}\n"
            f"🔢 **Кол-во:** {quantity_text}\n"
            f"📁 **Категория:** {cat_display}\n"
            f"✅ **Статус:** {'Куплено' if item.is_bought is not None else 'В списке'}\n\n"
            f"🆔 ID товара: {item.id}"
        )
        
        return response_text
    
    

    @staticmethod
    def format_category_item(item: ShoppingItem) -> str:
        amount_val = int(item.amount) if item.amount and item.amount.is_integer() else item.amount # type: ignore 
        quantity_text = f"{amount_val} {item.unit}" if item.amount else "" # type: ignore 

        response_text = (
            f"*{item.item} {quantity_text}*\n"
            f"ID товара: {item.id}"
        )
        return response_text
    
    @staticmethod
    def format_short_task(task: Task, is_day: bool) -> str:
        if is_day:
            deadline_time = (
                task.deadline_time.strftime('%H:%M')
                if task.deadline_time is not None else ""
            )

            answer = (
                f"{deadline_time} {task.description}\n"
                f"ID задачи: {task.id}"
            )
        else:
            deadline_day = task.deadline_day.strftime('%d-%m-%Y') if task.deadline_day is not None else ''
            deadline_time = task.deadline_time.strftime('%H-%M') if task.deadline_time is not None else ''

            answer = (
                f" {deadline_day} {deadline_time} {task.description}\n"
                f"ID задачи: {task.id}"
                )
        return answer
    
    @staticmethod
    def format_sub_info(sub: str) -> tuple[str, bool]:
        if sub == SubscriptionTypes.FREE:
            ans = (
                "У вас подписка free\n"
                "Вы можете хранить максимум 50 покупок и 50 задач\n"
                "Оформите Pro, чтобы не иметь ограничений в использовании сервиса"
            )
            return (ans, False)
        elif sub == SubscriptionTypes.PREMIUM:
            ans = (
                "У вас подписка Pro\n"
                "Вы можете пользоваться сервисом без ограничений"
            )
            return (ans, True)
        else:
            raise ValueError("Неизвестный тип подписки")

