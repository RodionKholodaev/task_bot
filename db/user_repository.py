from datetime import time
from sqlalchemy import select
from models import UserSettings
from db.database import get_session
from typing import Sequence
import logging

logger = logging.getLogger(__name__)


class UserRepository:

    @staticmethod
    async def get_all_users() -> Sequence[UserSettings] | None:

        async with get_session() as session:

            result = await session.execute(
                select(UserSettings)
            )

            return result.scalars().all()


    @staticmethod
    async def get_user_settings(user_id: int) -> UserSettings | None:
        """Получение настроек пользователя"""

        async with get_session() as session:

            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )

            return result.scalar_one_or_none()


    @staticmethod
    async def upsert_user_settings(user_id: int, utc_offset: int, notify_time: time):

        from scheduler.task_scheduler import create_daily_notification_job

        async with get_session() as session:

            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )

            settings = result.scalar_one_or_none()

            if settings:
                settings.utc_offset = utc_offset
                settings.notify_time = notify_time

            else:
                settings = UserSettings(
                    user_id=user_id,
                    utc_offset=utc_offset,
                    notify_time=notify_time
                )
                session.add(settings)

            await session.commit()

        try:
            create_daily_notification_job(
                user_id=user_id,
                utc_offset=utc_offset,
                notify_hour=notify_time.hour,
                notify_minute=notify_time.minute
            )
        except Exception as e:
            logger.error(
                f"Не удалось создать daily-джобу для пользователя {user_id}: {e}"
            )


    @staticmethod
    async def update_description(user_id: int, description: str):

        async with get_session() as session:

            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )

            settings = result.scalar_one_or_none()

            if settings:
                settings.self_description = description

            else:
                session.add(
                    UserSettings(
                        user_id=user_id,
                        self_description=description
                    )
                )

            await session.commit()


    @staticmethod
    async def get_description(user_id: int) -> str | None:

        async with get_session() as session:

            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )

            settings = result.scalar_one_or_none()

            if settings and settings.self_description:
                return settings.self_description

            return None