import re
from database import get_task_by_id, get_item_by_id, delete_item, delete_task, save_task, save_shopping_item
from .formater import Formater
from .parser import Parser
from models import Task, ShoppingItem

class MessageService:
    """
    создание сообщения от пользователя
    удадение сущности
    создание и сохранение новой сущности
    """
    
    # слишком много в одном методе
    @staticmethod
    def make_description(id: int, type: str, dt_string: str, request: str) -> str | None:
        if type == "tasks":
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
            return description
        elif type == "shopping_list":
            
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
            return description
        else:
            print("неизвестный тип (не задача, не покупка)")
            return None
        
    @staticmethod
    def delete_entity(id:int, type: str, user_id: int):
        if type == "tasks":
            delete_task(id, user_id)
        elif type == "shopping_list":
            delete_item(id, user_id)
        else:
            print("неизвестный тип (не задача, не покупка)")
            
    @staticmethod
    def make_save_new_entity(result: dict, type:str, user_id: int) -> Task | ShoppingItem | None:
        if type == "tasks":
            data = result["items"][0]

            data_time = Parser.parse_date(data)

            task = Task(
                user_id=user_id,
                description=data.get("task"),
                category=data.get("category", "short_30"),
                deadline_day=data_time["date"],
                deadline_time=data_time["time"],
                remind_time=data_time["remind_time"],
                remind_date=data_time["remind_date"]
            )

            # Сохраняем в БД
            save_task(task)
            return task
        elif type == "shopping_list":
            data = result["items"][0]

            # возможно будет ошибка с форматом!
            try:
                amount = float(data.get("amount"))
            except:
                amount = None

            item = ShoppingItem(
                user_id = user_id,
                category = data.get("category"),
                item = data.get("item"),
                amount = amount, # передаю строку, но алхимия преобразует во float
                unit = data.get("unit")
            )
            save_shopping_item(item)
            return item
        else:
            print("неизвестный тип (не задача, не покупка)")
            return None


