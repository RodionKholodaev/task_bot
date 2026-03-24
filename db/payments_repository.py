from typing import List
from sqlalchemy import select, update, and_
from models import Payment, UserAccount, SubscriptionTypes, UserSettings
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
# значения по умолчанию
UTC_OFFSET = 3
NOTIFY_TIME = datetime.strptime("08:00", "%H:%M").time()


class PaymentsRepository:

    @staticmethod
    async def get_started(s: AsyncSession, user_id: int):

        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        user_account = result.scalar_one_or_none()

        result = await s.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()

        if user_account is None:
            user_acc = UserAccount(
                user_id=user_id,
                task_count=0,
                item_count=0,
                subscription=SubscriptionTypes.FREE.name
            )
            s.add(user_acc)
            await s.commit()
            await s.refresh(user_acc)

        if user_settings is None:
            user_set = UserSettings(
                user_id=user_id,
                notify_time=NOTIFY_TIME,
                utc_offset=UTC_OFFSET
            )
            s.add(user_set)
            await s.commit()
            await s.refresh(user_set)


    @staticmethod
    async def save_payment(s: AsyncSession, user_id: int, tg_payment_id: str, provider_payment_id: str, amount: float):

        payment = Payment(
            user_id=user_id,
            amount=amount,
            status="succeeded",
            tg_payment_id=tg_payment_id,
            provider_payment_id=provider_payment_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )

        s.add(payment)

        await s.commit()

        await s.refresh(payment)


    @staticmethod
    async def change_user_sub(s: AsyncSession, user_id: int, new_sub: SubscriptionTypes) -> UserAccount | None:
        """Обновление типа подписки пользователя"""

        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )

        account = result.scalar_one_or_none()

        if account:

            account.subscription = new_sub

            if new_sub == SubscriptionTypes.PREMIUM:
                account.subscription_until = datetime.utcnow() + timedelta(days=30)
            else:
                account.subscription_until = None

            await s.commit()

            await s.refresh(account)

            return account

        return None


    @staticmethod
    async def get_user_sub(s: AsyncSession, user_id: int) -> SubscriptionTypes | None:

        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )

        account = result.scalar_one_or_none()

        if account:
            return account.subscription

        return None


    @staticmethod
    async def get_user_account(s: AsyncSession, user_id: int) -> UserAccount | None:

        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )

        return result.scalar_one_or_none()


    @staticmethod
    async def update_user_counter(s: AsyncSession, user_id: int, field: str, delta: int):
        """
        Универсальный инкремент/декремент.
        :param delta: целое число (например, 1 или -1)
        """
        # Словарь доступных полей для защиты от некорректного ввода
        field_map = {
            "tasks": UserAccount.task_count,
            "shopping_list": UserAccount.item_count
        }

        if field not in field_map:
            raise ValueError(f"Поле '{field}' не поддерживается")

        target_column = field_map[field]

        # Создаем базовое условие запроса
        filters = [UserAccount.user_id == user_id]

        # Если мы уменьшаем (delta < 0), добавляем проверку, чтобы не уйти ниже нуля
        if delta < 0:
            filters.append(target_column >= abs(delta))

        query = (
            update(UserAccount)
            .where(and_(*filters))
            .values({target_column: target_column + delta})
        )

        result = await s.execute(query)

        # Если rowcount == 0, значит юзер не найден или сработал предохранитель (ниже нуля)
        if result.rowcount < 0:
            raise ValueError(
                "Обновление не выполнено: пользователь не найден или недостаточное значение счетчика"
            )

        await s.commit()