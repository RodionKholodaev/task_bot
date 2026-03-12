from sqlalchemy import select, func, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from models import Task, ShoppingItem

class Statistics:
    
    @staticmethod
    async def get_productivity_score(session: AsyncSession, user_id: int):
        """
        Возвращает: Процент выполненных задач (float).
        Что значит: Общий показатель 'закрываемости' дел. 
        Помогает пользователю увидеть свою эффективность.
        """
        stmt = select(
            func.count(Task.id),
            func.sum(func.cast(Task.is_completed, Integer))
        ).where(Task.user_id == user_id)
        
        result = await session.execute(stmt)
        total, completed = result.one()
        
        if not total:
            return 0.0
        return round((completed / total) * 100, 1)

    @staticmethod
    async def get_top_task_categories(session: AsyncSession, user_id: int, limit: int = 3):
        """
        Возвращает: Список кортежей [(название_категории, количество)].
        Что значит: В каких сферах жизни у пользователя больше всего дел 
        (например, 'Работа' vs 'Личное').
        """
        stmt = (
            select(Task.category, func.count(Task.id))
            .where(Task.user_id == user_id)
            .group_by(Task.category)
            .order_by(func.count(Task.id).desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.all()

    @staticmethod
    async def get_shopping_habits(session: AsyncSession, user_id: int):
        """
        Возвращает: Словарь с топ-категорией и общим количеством купленного.
        Что значит: Позволяет понять, на что чаще всего направлено внимание 
        в покупках (например, 'Продукты' или 'Техника').
        """
        stmt = (
            select(ShoppingItem.category, func.count(ShoppingItem.id))
            .where(and_(ShoppingItem.user_id == user_id, ShoppingItem.is_bought == True))
            .group_by(ShoppingItem.category)
            .order_by(func.count(ShoppingItem.id).desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.first()
        return {"top_category": row[0] if row else "Нет данных", "total_bought": row[1] if row else 0}

    @staticmethod
    async def get_deadline_pressure(session: AsyncSession, user_id: int):
        """
        Возвращает: Количество просроченных невыполненных задач (int).
        Что значит: 'Критическая масса' дел, которые требуют немедленного внимания. 
        Полезно для алертов в разделе статистики.
        """
        today = datetime.utcnow().date()
        stmt = select(func.count(Task.id)).where(
            and_(
                Task.user_id == user_id,
                Task.is_completed == False,
                Task.deadline_day < today
            )
        )
        result = await session.execute(stmt)
        return result.scalar() or 0