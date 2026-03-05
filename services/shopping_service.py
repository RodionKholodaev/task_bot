from keyboards import PURCHASE_CATEGORY_MAP
from database import get_item_by_category
class ShoppingService:
    @staticmethod
    def get_category_item(user_id, category: str):

        category = PURCHASE_CATEGORY_MAP[category]
        item = get_item_by_category(user_id, category)
        
        return item
    