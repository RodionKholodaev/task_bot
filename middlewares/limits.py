from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from models import SubscriptionTypes
from aiogram.dispatcher.flags import get_flag

# Импортируйте ваши сессии БД и модели
from db.payments_repository import PaymentsRepository

from config import MAX_COUNT

class TaskLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # проверяем, что это хендлер для созданию задачи/покупки
        flag = get_flag(data, "long_operation")
        if flag != "check_limits":
            return await handler(event, data)
        
        # получаем ID пользователя
        if event.from_user is None:
            raise ValueError("У сообщения нет автора")

        user_id = event.from_user.id
        
        # достаем данные аккаунта (метод в репозитории)
        account = PaymentsRepository.get_user_account(user_id)
        
        if not account: # пускай хендлер сам разбирается
            return await handler(event, data)
        
        # для PREMIUM пользователя нет ограничений
        if account.subscription == SubscriptionTypes.PREMIUM: #type: ignore
            return await handler(event, data)

        if account.task_count + account.item_count >= MAX_COUNT: #type: ignore
            return await event.answer(
                f"❌ Лимит задач и покупак исчерпан (макс. {MAX_COUNT}). "
                "Удалите старые задачи и покупки или обновите подписку."
            )

        # если всё хорошо, передаем управление хендлеру
        return await handler(event, data)