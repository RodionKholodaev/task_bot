from datetime import date
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery # Импортируем типы
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserAccount

class UpdateActivityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        session = data.get("session")
        
        if not isinstance(event, (Message, CallbackQuery)) or event.from_user is None:
            return await handler(event, data)

        user_id = event.from_user.id
        
        # Проверяем наличие сессии 
        if isinstance(session, AsyncSession):
            today = date.today()
            
            # Используем session.get — это самый быстрый способ поиска по ID
            user = await session.get(UserAccount, user_id)

            if user and user.last_seen != today:
                user.last_seen = today
                await session.commit()
                # Прокидываем юзера дальше, чтобы не запрашивать в хендлере
                data["user"] = user

        return await handler(event, data)