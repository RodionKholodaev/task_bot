from typing import List
from sqlalchemy import select
from models import Payment, UserAccount, SubscriptionTypes, UserSettings
from db.database import get_session
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


    # Это не самый надежный код. Нет атомарности
    @staticmethod
    async def increment_counter(s: AsyncSession, user_id: int, field: str):

        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )

        user_acc = result.scalar_one_or_none()

        if user_acc is None:
            raise ValueError("Пользователь не найден")

        if field == "tasks":
            user_acc.task_count += 1

        elif field == "shopping_list":
            user_acc.item_count += 1

        await s.commit()