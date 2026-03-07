from typing import List
from models import ShoppingItem
from db.database import get_session

class ShoppingRepository:
    
    @staticmethod
    def save_shopping_item(shopping_item: ShoppingItem) -> ShoppingItem:
        """сохранение покупки"""
        s = get_session()
        try:
            s.add(shopping_item)
            s.commit()
            s.refresh(shopping_item)
            return shopping_item
        finally:
            s.close()


    @staticmethod
    def get_item_by_category(user_id: int, category: str) -> List[ShoppingItem]:
        s = get_session()
        try:
            return s.query(ShoppingItem).filter(
                ShoppingItem.user_id == user_id,
                ShoppingItem.category == category,
                ShoppingItem.is_bought == False
            ).all()
        finally:
            s.close()

    @staticmethod
    def get_item_by_id(item_id: int) -> ShoppingItem:
        """получение задачи по ее id"""
        s = get_session()
        try:
            return s.query(ShoppingItem).filter(ShoppingItem.id==item_id).first()
        finally:
            s.close()


    @staticmethod
    def mark_bought(item_id: int, user_id: int) -> bool:
        """Пометить предмет купленным"""
        s = get_session()
        try:
            item = s.query(ShoppingItem).filter_by(id=item_id, user_id=user_id).first()
            if not item:
                return False
            item.is_bought = True
            s.commit()
            return True
        finally:
            s.close()


    @staticmethod
    def delete_item(item_id: int, user_id: int) -> bool:
        """Удалить задачу"""
        s = get_session()
        try:
            item = s.query(ShoppingItem).filter_by(id=item_id, user_id=user_id).first()
            if not item:
                return False
            s.delete(item)
            s.commit()
            return True
        finally:
            s.close()

