from datetime import datetime, timedelta, timezone
import re

import logging
logger = logging.getLogger(__name__)

class Parser:
    """
    (преобразует один формат в другой)
    получает id и тип из сообщения
    формирует дату из строки
    переводит чисто из строки в float
    """
    @staticmethod
    def get_id_info(text) -> dict:
        logger.info("id и тип того что хочет изменить пользователь")
        # паттерн для ID товара 
        product_pattern = r"ID товара:\s*(?P<id>\d+)"
        
        # паттерн для ID задачи 
        task_pattern = r"ID задачи:\s*(?P<id>\d+)"
        
        # проверяем на товар
        product_match = re.search(product_pattern, text)
        if product_match:
            return {"id": product_match.group("id"), "type": "shopping_list"}
        
        # проверяем на задачу
        task_match = re.search(task_pattern, text)
        if task_match:
            return {"id": task_match.group("id"), "type": "tasks"}
        logger.error("ID не найден в сообщении!")
        raise ValueError(f"ID не найден в сообщении: {text}")

    
