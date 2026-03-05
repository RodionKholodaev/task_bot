from datetime import datetime, timedelta, timezone
from database import get_user_settings
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

    
    @staticmethod
    def parse_date(data: dict) -> dict:
        # превращает строку в объект datetime
        # Безопасное извлечение даты и времени
        logger.info("получаю дату из ответа LLM")
        try:
            deadline_day = datetime.strptime(data["date"], "%Y-%m-%d").date() if data.get("date") else None
        except (ValueError, TypeError):
            deadline_day = None

        try:
            print(f"пытаюсь получить время")
            time_str = data.get("time")
            print(f"получил {time_str}")
            deadline_time = datetime.strptime(time_str, "%H:%M").time() if time_str else None
            print(f"после перевода в во время: {deadline_time}")
        except (ValueError, TypeError):
            print("попал в exception в time")
            deadline_time = None
        
        try:
            print("начал работать с remind_date")
            remind_date_str=data.get("remind_date")
            remind_date=datetime.strptime(remind_date_str, "%Y-%m-%d").date() if remind_date_str else None
            print(remind_date)
        except Exception as e:
            print(f"попал в exception в remind_date, ошибка: {e}")
            remind_date=None

        try:
            print(f"пытаюсь получить время напоминания")
            remind_time_str=data.get("remind_time")
            print(f"получил {remind_time_str}")
            remind_time=datetime.strptime(remind_time_str, "%H:%M").time() if remind_time_str else None
            print(f"после перевода в во время: {remind_time}")
        except:
            print("попал в exception в remind_time")
            remind_time=None
        
        ans={
            "date": deadline_day,
            "time": deadline_time,
            "remind_date": remind_date,
            "remind_time": remind_time
            }
        logger.debug(f"итоговый словарь со временем: {ans}")
        
        return ans
    
    @staticmethod
    def parse_num(str_num: str) -> float | None:
        try:
            if str_num == "": return None
            else: return float(str_num)
        except:
            print(f"Нейросеть в поле для числа вернула символ(ы): {str_num}")
            return None
