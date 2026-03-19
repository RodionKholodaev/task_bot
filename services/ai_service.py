from ai.ai_client import parse_text, edit_entity
from db.user_repository import UserRepository
class AiService:
    @staticmethod
    def ai_parse(description: str, user_id:int):
        """вызов функции парсинга нейросетью и проверка подписки"""
        user_description = UserRepository.get_description(user_id)
        if user_description is None: user_description = "описания пользователя нет"
        return parse_text(description, user_description)

    @staticmethod
    def ai_edit(description: str, date_and_time: str, user_id):
        """вызов функции редактирования и проверка подписки"""
        user_description = UserRepository.get_description(user_id)
        if user_description is None: user_description = "описания пользователя нет"
        return edit_entity(description, date_and_time, user_description)
        


