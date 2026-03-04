from datetime import date, time
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DB_URL
from models import Base, Task, UserSettings, ShoppingItem

# инициализация БД
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Создание таблиц при запуске"""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Получение сессии БД"""
    return SessionLocal()


# ================= CRUD операции =================
def get_all_users() -> UserSettings | None:
    s=get_session()
    try:
        return s.query(UserSettings).all()
    finally:
        s.close()

def get_user_settings(user_id: int) -> UserSettings | None:
    """Получение настроек пользователя"""
    s = get_session()
    try:
        return s.query(UserSettings).filter_by(user_id=user_id).first()
    finally:
        s.close()




def upsert_user_settings(user_id: int, utc_offset: int, notify_time: time):
    """Обновление/создание настроек пользователя"""
    s = get_session()
    try:
        settings = s.query(UserSettings).filter_by(user_id=user_id).first()
        if settings:
            settings.utc_offset = utc_offset
            settings.notify_time = notify_time
        else:
            s.add(UserSettings(
                user_id=user_id,
                utc_offset=utc_offset,
                notify_time=notify_time
            ))
        s.commit()
    finally:
        s.close()


def save_task(task: Task) -> Task:
    """Сохранение задачи"""
    s = get_session()
    try:
        s.add(task)
        s.commit()
        s.refresh(task)
        return task
    finally:
        s.close()

def save_shopping_item(shopping_item: ShoppingItem) -> ShoppingItem:
    """сохранение покупки"""
    s = get_session()
    try:
        s.add(shopping_item)
        s.commit()
        s.refresh(shopping_item)
        return shopping_item
    finally:
        s.close()



def get_tasks_for_day(user_id: int, day: date) -> List[Task]:
    """Получение задач на указаный день"""
    s = get_session()
    try:
        return s.query(Task).filter(
            Task.user_id == user_id,
            Task.deadline_day == day,
            Task.is_completed == False
        ).order_by(Task.deadline_time).all()
    finally:
        s.close()


def get_tasks_week(user_id: int, start: date, end: date) -> List[Task]:
    """Получение задач на неделю"""
    s = get_session()
    try:
        return s.query(Task).filter(
            Task.user_id == user_id,
            Task.deadline_day >= start,
            Task.deadline_day <= end,
            Task.is_completed == False
        ).order_by(Task.deadline_day).all()
    finally:
        s.close()

def get_tasks_to_remind(user_id: int) -> List[Task]:
    s = get_session()
    try:
        return s.query(Task).filter(
                    Task.user_id == user_id,
                    Task.is_completed == False,
                    Task.remind_date.isnot(None)  # Напоминание установлено
                ).all()
    finally:
        s.close()


def get_tasks_by_category(user_id: int, category: str) -> List[Task]:
    s = get_session()
    try:
        return s.query(Task).filter(
            Task.user_id == user_id,
            Task.category == category,
            Task.is_completed == False
        ).all()
    finally:
        s.close()


def get_item_by_category(user_id: int, category: str) -> List[ShoppingItem]:
    s = get_session()
    try:
        return s.query(ShoppingItem).filter(
            ShoppingItem.user_id == user_id,
            ShoppingItem.category == category,
            ShoppingItem.is_bought == False
        ).all()
    finally:
        s.close()

def get_item_by_id(item_id: int) -> ShoppingItem:
    """получение задачи по ее id"""
    s = get_session()
    try:
        return s.query(ShoppingItem).filter(ShoppingItem.id==item_id).first()
    finally:
        s.close()

def get_task_by_id(task_id: int) -> Task:
    """получение задачи по ее id"""
    s = get_session()
    try:
        return s.query(Task).filter(Task.id==task_id).first()
    finally:
        s.close()

def get_all_tasks(user_id: int) -> List[Task]:
    """Получение всех задач пользователя"""
    s = get_session()
    try:
        return s.query(Task).filter(Task.user_id == user_id, Task.is_completed==False).all()
    finally:
        s.close()


def mark_done(task_id: int, user_id: int) -> bool:
    """Пометить задачу выполненой"""
    s = get_session()
    try:
        task = s.query(Task).filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return False
        task.is_completed = True
        s.commit()
        return True
    finally:
        s.close()


def mark_bought(item_id: int, user_id: int) -> bool:
    """Пометить предмет купленным"""
    s = get_session()
    try:
        item = s.query(ShoppingItem).filter_by(id=item_id, user_id=user_id).first()
        if not item:
            return False
        item.is_bought = True
        s.commit()
        return True
    finally:
        s.close()

def delete_task(task_id: int, user_id: int) -> bool:
    """Удалить задачу"""
    s = get_session()
    try:
        task = s.query(Task).filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return False
        s.delete(task)
        s.commit()
        return True
    finally:
        s.close()

def delete_item(item_id: int, user_id: int) -> bool:
    """Удалить задачу"""
    s = get_session()
    try:
        item = s.query(ShoppingItem).filter_by(id=item_id, user_id=user_id).first()
        if not item:
            return False
        s.delete(item)
        s.commit()
        return True
    finally:
        s.close()

