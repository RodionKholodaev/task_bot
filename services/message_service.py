import re
from database import get_task_by_id, get_item_by_id, delete_item, delete_task, save_task, save_shopping_item
from .formater import Formater
from .parser import Parser
from models import Task, ShoppingItem
from ai.schemas import ItemLLMResponse, TaskLLMResponse
import logging
logger = logging.getLogger(__name__)

class MessageService:
    """
    удадение сущности
    создание и сохранение новой сущности
    """

    @staticmethod
    def delete_entity(id:int, type: str, user_id: int):
        if type == "tasks":
            delete_task(id, user_id)
        elif type == "shopping_list":
            delete_item(id, user_id)
        else:
            logger.error(f"неизвестный тип для удаления: {type}")
            raise ValueError(f"неизвестная сущность {type}")
            
    @staticmethod
    def make_save_new_entity(result: dict, user_id: int) -> Task | ShoppingItem | None:
        if result["type"] == "tasks":
            data = result["items"][0]

            val_data = TaskLLMResponse(**data)

            task = Task(
                user_id=user_id,
                description=val_data.task,
                category=val_data.category,
                deadline_day=val_data.deadline_date,
                deadline_time=val_data.deadline_time,
                remind_time=val_data.remind_time,
                remind_date=val_data.remind_date
            )
            logger.debug("создал задачу")
            # Сохраняем в БД
            save_task(task)
            logger.debug("сохранил задачу")
            return task
        elif result["type"] == "shopping_list":
            data = result["items"][0]

            val_data = ItemLLMResponse(**data)

            item = ShoppingItem(
                user_id = user_id,
                category = val_data.category,
                item = val_data.item,
                amount = val_data.amount, # передаю строку, но алхимия преобразует во float
                unit = val_data.unit
            )
            logger.debug("создал покупку")
            save_shopping_item(item)
            logger.debug("сохранил покупку")
            return item
        else:
            logger.error(f"попытка создать неизвестный тип! {result["type"]}")
            raise ValueError(f"попытка создать неизвестный тип! {result["type"]}")



