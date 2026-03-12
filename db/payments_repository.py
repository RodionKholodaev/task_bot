from typing import List
from models import Payment, UserAccount, SubscriptionTypes, UserSettings
from db.database import get_session

from datetime import datetime, timedelta

# значения по умолчанию
MAX_TASK_COUNT = 50
MAX_ITEM_COUNT = 50
UTC_OFFSET = 3
NOTIFY_TIME = datetime.strptime("08:00", "%H:%M").time()

class PaymentsRepository:

    @staticmethod
    def get_started(user_id: int):
        s = get_session()
        user_account = s.query(UserAccount).filter_by(user_id= user_id).first()
        user_settings = s.query(UserSettings).filter_by(user_id = user_id).first()
        if user_account is None:
            user_acc = UserAccount(
                user_id = user_id,
                task_count = MAX_TASK_COUNT,
                item_count = MAX_ITEM_COUNT,
                subscription = SubscriptionTypes.FREE.name
            )
            s.add(user_acc)
            s.commit()
            s.refresh(user_acc)
        if user_settings is None:
            user_set = UserSettings(
                user_id = user_id,
                notify_time = NOTIFY_TIME,
                utc_offset = UTC_OFFSET
            )
            s.add(user_set)
            s.commit()
            s.refresh(user_set)

        return


    @staticmethod
    def save_payment(user_id: int, tg_payment_id: str, provider_payment_id: str, amount: float):
        s = get_session()
        try:
            payment = Payment(
                user_id = user_id,
                amount = amount,
                status = "succeeded",
                tg_payment_id = tg_payment_id,
                provider_payment_id = provider_payment_id,
                created_at = datetime.now(),
                expires_at = datetime.now() + timedelta(days=30)
            )
            s.add(payment)
            s.commit()
            s.refresh(payment)
        finally:
            s.close()

    @staticmethod
    def change_user_sub(user_id: int, new_sub: SubscriptionTypes) -> UserAccount | None:
        """Обновление типа подписки пользователя"""
        s = get_session()
        try:
            # 1. Получаем запись
            account = s.query(UserAccount).filter_by(user_id=user_id).first()
            
            if account:
                # 2. Обновляем тип подписки
                account.subscription = new_sub #type: ignore
                
                # 3. Логика даты: если Premium — ставим +30 дней, если Free — зануляем
                if new_sub == SubscriptionTypes.PREMIUM:
                    account.subscription_until = datetime.utcnow() + timedelta(days=30) #type: ignore
                else:
                    account.subscription_until = None #type: ignore
                
                s.commit()
                s.refresh(account)
                return account
            
            return None
        finally:
            s.close()

    @staticmethod
    def get_user_sub(user_id: int) -> str | None:
        s = get_session()
        try:
            account = s.query(UserAccount).filter_by(user_id = user_id).first()
            if account:
                sub = account.subscription
                return sub # type: ignore
            else:
                return None
        finally:
            s.close()