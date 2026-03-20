from ai.ai_client import parse_text, edit_entity
from db.user_repository import UserRepository
class AiService:
    @staticmethod
    async def ai_parse(description: str, user_id:int, session):
        """вызов функции парсинга нейросетью и проверка подписки"""
        user_description = await UserRepository.get_description(session, user_id)
        if user_description is None: user_description = "описания пользователя нет"
        return await parse_text(description, user_description)

    @staticmethod
    async def ai_edit(description: str, date_and_time: str, user_id, session):
        """вызов функции редактирования и проверка подписки"""
        user_description = await UserRepository.get_description(session, user_id)
        if user_description is None: user_description = "описания пользователя нет"
        return await edit_entity(description, date_and_time, user_description)
        


