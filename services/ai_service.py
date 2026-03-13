from ai.ai_client import parse_text, edit_entity
class AiService:
    @staticmethod
    def ai_parse(description: str, user_id):
        """вызов функции парсинга нейросетью и проверка подписки"""
        return parse_text(description)

    @staticmethod
    def ai_edit(description: str, date_and_time: str, user_id):
        """вызов функции редактирования и проверка подписки"""
        return edit_entity(description, date_and_time)
        


