import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, Float, Enum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Task(Base):
    """Модель для задачи"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    deadline_day = Column(Date, nullable=True)
    deadline_time = Column(Time, nullable=True)

    remind_date = Column(Date, nullable=True)
    remind_time = Column(Time, nullable=True)

class ShoppingItem(Base):
    """Модель для конкретного товара в списке покупок"""
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Суть покупки
    item = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True) # "Продукты", "Аптека" и т.д.
    
    # Количественные характеристики
    amount = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True) # кг, мл, упак.
    
    # Состояние
    is_bought = Column(Boolean, default=False)
    
    # Таймстампы
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class SubscriptionTypes(enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


print(SubscriptionTypes.FREE)

class UserSettings(Base):
    """Модель пользователя"""
    __tablename__ = "user_settings"

    user_id = Column(Integer, primary_key=True)
    utc_offset = Column(Integer, nullable=False)
    notify_time = Column(Time, nullable=False)
    self_description = Column(String(500), nullable=True) 


class UserAccount(Base):

    __tablename__="user_account"

    user_id = Column(Integer, primary_key=True)
    task_count = Column(Integer, default=50) # нужно увеличивать и уменьшать кода нужно
    item_count = Column(Integer, default=50) # нужно увеличивать и уменьшать кода нужно

    subscription = Column(Enum(SubscriptionTypes),default=SubscriptionTypes.FREE, nullable=False )
    subscription_until = Column(DateTime, nullable=True)

# платежи
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Integer)
    status = Column(String)
    tg_payment_id = Column(String)
    provider_payment_id = Column(String)
    
    created_at = Column(DateTime)
    expires_at = Column(DateTime) # когда подписка истекает


