from datetime import datetime, timedelta, timezone
from database import get_user_settings
class Parser:
    """
    формирует дату и время для отдачи в промте для нейросети
    формирует дату из строки
    переводит чисто из строки в float
    """
    @staticmethod
    def get_user_time(user_id: int) -> str | None:
        
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

        print(f"день, дата и время для передачи в нейросеть: {dt_string}")
        return dt_string

    @staticmethod
    def parse_date(data: dict) -> dict:
        # превращает строку в объект datetime
        # Безопасное извлечение даты и времени
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
        

        return ans
    
    @staticmethod
    def parse_num(str_num: str) -> float | None:
        try:
            if str_num == "": return None
            else: return float(str_num)
        except:
            print(f"Нейросеть в поле для числа вернула символ(ы): {str_num}")
            return None
