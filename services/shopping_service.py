from keyboards import PURCHASE_CATEGORY_MAP
from db.shopping_repository import ShoppingRepository

import logging
logger = logging.getLogger(__name__)

class ShoppingService:
    @staticmethod
    def get_category_item(user_id, category: str):
        logger.info("получаю покупки по категории")
        category = PURCHASE_CATEGORY_MAP[category]
        items = ShoppingRepository.get_item_by_category(user_id, category)
        
        return items
    