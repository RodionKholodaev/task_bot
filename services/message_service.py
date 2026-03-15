import re
from db.task_repository import TaskRepository
from db.shopping_repository import ShoppingRepository
from db.payments_repository import PaymentsRepository
from db.user_repository import UserRepository
from .formater import Formater
from .parser import Parser
from models import Task, ShoppingItem
from ai.schemas import ItemLLMResponse, TaskLLMResponse
from typing import List
from scheduler.task_scheduler import create_task_reminder_job, create_daily_notification_job
import logging
logger = logging.getLogger(__name__)

class MessageService:
    """
    удадение сущности
    создание и сохранение новой сущности
    """

    @staticmethod
    async def delete_entity(id:int, type: str, user_id: int):
        if type == "tasks":
            await TaskRepository.delete_task(id, user_id)
        elif type == "shopping_list":
            await ShoppingRepository.delete_item(id, user_id)
        else:
            logger.error(f"неизвестный тип для удаления: {type}")
            raise ValueError(f"неизвестная сущность {type}")
            
    @staticmethod
    async def make_save_new_entity(result: dict, user_id: int) -> List[Task] | List[ShoppingItem] | None:
        settings = UserRepository.get_user_settings(user_id)
        if settings is None:
            raise ValueError("пользователь не найден")
            
        if result["type"] == "tasks":
            tasks = []
            for data in result["items"]:
                await PaymentsRepository.increment_counter(user_id, field="tasks")
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
                
                # сначала сохраняем в БД
                await TaskRepository.save_task(task)
                logger.debug("сохранил задачу")
                
                # потом создаём джобу напоминания (если есть remind_date)
                if task.remind_date is not None:
                    create_task_reminder_job(
                        user_id=user_id,
                        task_id=task.id,  #type: ignore
                        remind_date=task.remind_date,#type: ignore
                        remind_time=task.remind_time,#type: ignore
                        notify_time=settings.notify_time,#type: ignore
                        utc_offset=settings.utc_offset #type: ignore
                    )
                
                tasks.append(task)

            
            return tasks
        
        elif result["type"] == "shopping_list":
            items = []
            for data in result["items"]:
                await PaymentsRepository.increment_counter(user_id, field="shopping_list")
                val_data = ItemLLMResponse(**data)

                item = ShoppingItem(
                    user_id = user_id,
                    category = val_data.category,
                    item = val_data.item,
                    amount = val_data.amount, # передаю строку, но алхимия преобразует во float
                    unit = val_data.unit
                )
                logger.debug("создал покупку")
                await ShoppingRepository.save_shopping_item(item)
                logger.debug("сохранил покупку")
                items.append(item)
            
            return items
        else:
            logger.error(f"попытка создать неизвестный тип! {result["type"]}")
            raise ValueError(f"попытка создать неизвестный тип! {result["type"]}")



