from sqlalchemy import select, func, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from models import Task, ShoppingItem, UserAccount # Добавил UserAccount

class Statistics:
    
    @staticmethod
    async def get_productivity_score(session: AsyncSession, user_id: int):
        stmt = select(
            func.count(Task.id),
            func.sum(func.cast(Task.is_completed, Integer))
        ).where(Task.user_id == user_id)
        
        result = await session.execute(stmt)
        total, completed = result.one()
        
        # completed может быть None, если задач нет совсем
        completed = completed or 0 
        
        if not total:
            return 0.0
        return round((completed / total) * 100, 1)

    @staticmethod
    async def get_top_task_categories(session: AsyncSession, user_id: int, limit: int = 3):
        stmt = (
            select(Task.category, func.count(Task.id))
            .where(Task.user_id == user_id)
            .group_by(Task.category)
            .order_by(func.count(Task.id).desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        # Фильтруем категории, которые вдруг оказались None
        return [(cat, count) for cat, count in result.all() if cat]

    @staticmethod
    async def get_shopping_habits(session: AsyncSession, user_id: int):
        stmt = (
            select(ShoppingItem.category, func.count(ShoppingItem.id))
            .where(and_(ShoppingItem.user_id == user_id, ShoppingItem.is_bought == True))
            .group_by(ShoppingItem.category)
            .order_by(func.count(ShoppingItem.id).desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.first()
        
        top_cat = row[0] if row and row[0] else "Нет данных"
        total_bought = row[1] if row and row[1] else 0
        
        return {"top_category": top_cat, "total_bought": total_bought}

    @staticmethod
    async def get_deadline_pressure(session: AsyncSession, user_id: int):
        # Используем timezone-aware datetime для корректности, но приводим к date
        today = datetime.now(timezone.utc).date()
        
        stmt = select(func.count(Task.id)).where(
            and_(
                Task.user_id == user_id,
                Task.is_completed == False,
                Task.deadline_day < today
            )
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def get_account_info(session: AsyncSession, user_id: int):
        """Получает информацию о подписке и лимитах"""
        stmt = select(UserAccount).where(UserAccount.user_id == user_id)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            return {"sub": "Free", "tasks_limit": 50, "items_limit": 50}
            
        return {
            "sub": account.subscription.value.upper(),
            "tasks_limit": account.task_count,
            "items_limit": account.item_count
        }