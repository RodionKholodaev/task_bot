from keyboards import PURCHASE_CATEGORY_MAP
from db.shopping_repository import ShoppingRepository
from sqlalchemy.ext.asyncio import AsyncSession
import logging
logger = logging.getLogger(__name__)

class ShoppingService:
    @staticmethod
    def get_category_item(s: AsyncSession, user_id, category: str):
        logger.info("получаю покупки по категории")
        category = PURCHASE_CATEGORY_MAP[category]
        items = ShoppingRepository.get_item_by_category(s, user_id, category)
        
        return items
    