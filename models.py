from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time
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

    message_id = Column(Integer, nullable=True)



class UserSettings(Base):
    """Модель пользователя"""
    __tablename__ = "user_settings"

    user_id = Column(Integer, primary_key=True)
    utc_offset = Column(Integer, nullable=False)
    notify_time = Column(Time, nullable=False)

