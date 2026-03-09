from datetime import time
from models import UserSettings
from db.database import get_session
from typing import List
class UserRepository:

    @staticmethod
    def get_all_users() -> List[UserSettings] | None:
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
                settings.utc_offset = utc_offset # type: ignore
                settings.notify_time = notify_time # type: ignore
            else:
                s.add(UserSettings(
                    user_id=user_id,
                    utc_offset=utc_offset,
                    notify_time=notify_time
                ))
            s.commit()
        finally:
            s.close()

    @staticmethod
    def update_description(user_id: int, description: str):
        s = get_session()
        try:
            settings = s.query(UserSettings).filter_by(user_id=user_id).first()
            if settings:
                settings.self_description = description # type: ignore
            else:
                s.add(UserSettings(
                    user_id=user_id,
                    self_description = description
                ))
            s.commit()
        finally:
            s.close()

    @staticmethod
    def get_description(user_id: int) ->  str | None:
        """Получение настроек пользователя"""
        s = get_session()
        try:
            settings = s.query(UserSettings).filter_by(user_id=user_id).first()
            if settings is None:
                return None
            else:
                if settings.self_description is not None:
                    return settings.self_description # type: ignore
                return None
        finally:
            s.close()