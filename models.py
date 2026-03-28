import enum
from datetime import datetime, date, time
from typing import Optional

from sqlalchemy import String, DateTime, Date, Time, Float, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Определяем базовый класс
class Base(DeclarativeBase):
    pass

class SubscriptionTypes(enum.Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"

class Task(Base):
    """Модель для задачи"""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Используем BigInteger для Telegram ID, так как они могут превысить 2^31-1
    user_id: Mapped[int] = mapped_column(index=True, nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)
    is_completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    deadline_day: Mapped[Optional[date]] = mapped_column(Date)
    deadline_time: Mapped[Optional[time]] = mapped_column(Time)

    remind_date: Mapped[Optional[date]] = mapped_column(Date)
    remind_time: Mapped[Optional[time]] = mapped_column(Time)

class ShoppingItem(Base):
    """Модель для товара в списке покупок"""
    __tablename__ = "shopping_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    
    item: Mapped[str] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    
    amount: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    
    is_bought: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

class UserSettings(Base):
    """Настройки пользователя"""
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    utc_offset: Mapped[int] = mapped_column(nullable=False)
    notify_time: Mapped[time] = mapped_column(Time, nullable=False)
    self_description: Mapped[Optional[str]] = mapped_column(String(500))

class UserAccount(Base):
    """Аккаунт и статистика пользователя"""
    __tablename__ = "user_account"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    task_count: Mapped[int] = mapped_column(default=0)
    item_count: Mapped[int] = mapped_column(default=0)

    
    subscription: Mapped[SubscriptionTypes] = mapped_column(
        Enum(SubscriptionTypes), 
        default=SubscriptionTypes.FREE
    )
    
    subscription_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    referrer_id: Mapped[Optional[int]] = mapped_column(index=True, nullable=True)

    last_seen: Mapped[date] = mapped_column(
            Date, 
            default=date.today,
            index=True
        )

class Payment(Base):
    """История платежей"""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    amount: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column()
    tg_payment_id: Mapped[str] = mapped_column()
    provider_payment_id: Mapped[str] = mapped_column()
    
    created_at: Mapped[datetime] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column()