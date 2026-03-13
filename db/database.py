from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DB_URL
from models import Base

# инициализация БД
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Создание таблиц при запуске"""
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """Получение сессии БД"""
    return SessionLocal()


