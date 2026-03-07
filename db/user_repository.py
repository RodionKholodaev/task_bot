from datetime import time
from models import UserSettings
from db.database import get_session

class UserRepository:

    @staticmethod
    def get_all_users() -> UserSettings | None:
        s=get_session()
        try:
            return s.query(UserSettings).all()
        finally:
            s.close()

    @staticmethod
    def get_user_settings(user_id: int) -> UserSettings | None:
        """Получение настроек пользователя"""
        s = get_session()
        try:
            return s.query(UserSettings).filter_by(user_id=user_id).first()
        finally:
            s.close()

    @staticmethod
    def upsert_user_settings(user_id: int, utc_offset: int, notify_time: time):
        """Обновление/создание настроек пользователя"""
        s = get_session()
        try:
            settings = s.query(UserSettings).filter_by(user_id=user_id).first()
            if settings:
                settings.utc_offset = utc_offset
                settings.notify_time = notify_time
            else:
                s.add(UserSettings(
                    user_id=user_id,
                    utc_offset=utc_offset,
                    notify_time=notify_time
                ))
            s.commit()
        finally:
            s.close()




