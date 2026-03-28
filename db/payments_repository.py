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
    async def get_started(s: AsyncSession, user_id: int, referrer_id: int | None = None, bot = None): # Добавили аргумент
        # Проверяем аккаунт
        result = await s.execute(select(UserAccount).where(UserAccount.user_id == user_id))
        user_account = result.scalar_one_or_none()

        # Проверяем настройки
        result = await s.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        user_settings = result.scalar_one_or_none()

        if user_account is None:
            user_account = UserAccount(
                user_id=user_id,
                task_count=0,
                item_count=0,
                subscription=SubscriptionTypes.FREE,
                referrer_id=referrer_id
            )
            s.add(user_account)
            
            # НОВЫЙ БЛОК: Если есть пригласитель, начисляем ему бонус
            if referrer_id and bot:
                await PaymentsRepository.add_referral_bonus(s, referrer_id, bot)

        if user_settings is None:
            user_settings = UserSettings(
                user_id=user_id,
                notify_time=NOTIFY_TIME,
                utc_offset=UTC_OFFSET
            )
            s.add(user_settings)

        await s.commit() # Один коммит на всё


    @staticmethod
    async def add_referral_bonus(s: AsyncSession, referrer_id: int, bot):
        """Начисляет 7 дней Premium пригласившему"""
        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == referrer_id)
        )
        referrer_account = result.scalar_one_or_none()

        if referrer_account:
            # Если подписки нет или она просрочена, начинаем от "сейчас"
            # Если активна — прибавляем к дате окончания
            start_date = (
                referrer_account.subscription_until 
                if (referrer_account.subscription_until and referrer_account.subscription_until > datetime.utcnow()) 
                else datetime.utcnow()
            )
            
            referrer_account.subscription = SubscriptionTypes.PREMIUM
            referrer_account.subscription_until = start_date + timedelta(days=7)
            
            # Уведомляем счастливчика
            try:
                await bot.send_message(
                    referrer_id, 
                    "🎉 По вашей ссылке присоединился новый пользователь! Вам начислено 7 дней Premium-подписки."
                )
            except Exception:
                pass # Если заблокировал бота


    @staticmethod
    async def save_payment(s: AsyncSession, user_id: int, tg_payment_id: str, provider_payment_id: str, amount: float):

        payment = Payment(
            user_id=user_id,
            amount=amount,
            status="succeeded",
            tg_payment_id=tg_payment_id,
            provider_payment_id=provider_payment_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
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
                start_date = account.subscription_until if (account.subscription_until and account.subscription_until > datetime.utcnow()) else datetime.utcnow()
                account.subscription_until = start_date + timedelta(days=30)
            else:
                account.subscription_until = None

            await s.commit()

            await s.refresh(account)

            return account

        return None


    @staticmethod
    async def get_user_sub(s: AsyncSession, user_id: int) -> SubscriptionTypes:
        result = await s.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            return SubscriptionTypes.FREE

        # Если подписка PREMIUM, но время вышло — сбрасываем в FREE
        if account.subscription == SubscriptionTypes.PREMIUM:
            if account.subscription_until and account.subscription_until < datetime.utcnow():
                account.subscription = SubscriptionTypes.FREE
                account.subscription_until = None
                await s.commit()
                return SubscriptionTypes.FREE

        return account.subscription

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