from datetime import datetime, timedelta, timezone
from database import get_user_settings
class task_service():
    @staticmethod
    def get_user_time(user_id : int) -> str | None:
        settings = get_user_settings(user_id)
        if not settings:
            return None
        else:
            # Получаем дату в часовом поясе пользователя
            user_tz = timezone(timedelta(hours=settings.utc_offset))
            user_datetime = datetime.now(user_tz)
            dt_string = user_datetime.strftime("%Y-%m-%d %H:%M")
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
            time_str = data.get("time")
            deadline_time = datetime.strptime(time_str, "%H:%M").time() if time_str else None
        except (ValueError, TypeError):
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
            remind_time_str=data.get("remind_time")
            remind_time=datetime.strptime(remind_time_str, "%H:%M").time() if remind_time_str else None
        except:
            remind_time=None
        
        ans={
            "date": deadline_day,
            "time": deadline_time,
            "remind_date": remind_date,
            "remind_time": remind_time
            }
        

        return ans
    
