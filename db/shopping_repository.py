from typing import Sequence
from sqlalchemy import select
from models import ShoppingItem
from db.database import get_session


class ShoppingRepository:

    @staticmethod
    async def save_shopping_item(shopping_item: ShoppingItem) -> ShoppingItem:
        """сохранение покупки"""

        async with get_session() as s:

            s.add(shopping_item)

            await s.commit()

            # refresh нужен если id генерируется БД
            await s.refresh(shopping_item)

            return shopping_item


    @staticmethod
    async def get_item_by_category(user_id: int, category: str) -> Sequence[ShoppingItem]:

        async with get_session() as s:

            result = await s.execute(
                select(ShoppingItem).where(
                    ShoppingItem.user_id == user_id,
                    ShoppingItem.category == category,
                    ShoppingItem.is_bought == False
                )
            )

            return result.scalars().all()


    @staticmethod
    async def get_item_by_id(item_id: int) -> ShoppingItem | None:
        """получение задачи по ее id"""

        async with get_session() as s:

            result = await s.execute(
                select(ShoppingItem).where(ShoppingItem.id == item_id)
            )

            return result.scalar_one_or_none()


    @staticmethod
    async def mark_bought(item_id: int, user_id: int) -> bool:
        """Пометить предмет купленным"""

        async with get_session() as s:

            result = await s.execute(
                select(ShoppingItem).where(
                    ShoppingItem.id == item_id,
                    ShoppingItem.user_id == user_id
                )
            )

            item = result.scalar_one_or_none()

            if not item:
                return False

            item.is_bought = True

            await s.commit()

            return True


    @staticmethod
    async def delete_item(item_id: int, user_id: int) -> bool:
        """Удалить задачу"""

        async with get_session() as s:

            result = await s.execute(
                select(ShoppingItem).where(
                    ShoppingItem.id == item_id,
                    ShoppingItem.user_id == user_id
                )
            )

            item = result.scalar_one_or_none()

            if not item:
                return False

            await s.delete(item)

            await s.commit()

            return True