# bot.py
import asyncio
import os
from datetime import datetime
from typing import List, Dict

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from ai_client import classify_task  # наша функция работы с OpenRouter

# ---------- Конфиг ----------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")

DB_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db")

# ---------- БД ----------

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)  # short_5, short_30, short_120, long
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def create_task(user_id: int, description: str, category: str) -> Task:
    session: Session = SessionLocal()
    try:
        task = Task(
            user_id=user_id,
            description=description,
            category=category,
            is_completed=False,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    finally:
        session.close()


def get_tasks_by_category(user_id: int, category: str) -> List[Task]:
    session: Session = SessionLocal()
    try:
        tasks = (
            session.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.category == category,
                Task.is_completed == False,
            )
            .order_by(Task.created_at.asc())
            .all()
        )
        return tasks
    finally:
        session.close()


# Здесь можно будет реализовать пометку выполненной и удаление:
def mark_task_completed(task_id: int, user_id: int) -> bool:
    session: Session = SessionLocal()
    try:
        task = session.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id,
        ).first()
        if not task:
            return False
        task.is_completed = True
        session.commit()
        return True
    finally:
        session.close()


def delete_task(task_id: int, user_id: int) -> bool:
    session: Session = SessionLocal()
    try:
        task = session.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id,
        ).first()
        if not task:
            return False
        session.delete(task)
        session.commit()
        return True
    finally:
        session.close()


# ---------- Клавиатура ----------

def main_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с фильтрами задач.
    """
    btn_5 = KeyboardButton(text="≤ 5 минут")
    btn_30 = KeyboardButton(text="≤ 30 минут")
    btn_120 = KeyboardButton(text="≤ 2 часов")
    btn_long = KeyboardButton(text="Сложные задачи")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [btn_5, btn_30],
            [btn_120, btn_long],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


# ---------- Утилиты ----------

CATEGORY_LABELS: Dict[str, str] = {
    "short_5": "≤ 5 минут",
    "short_30": "≤ 30 минут",
    "short_120": "≤ 2 часов",
    "long": "Сложные задачи",
}


def category_from_button(text: str) -> str | None:
    for key, label in CATEGORY_LABELS.items():
        if text == label:
            return key
    return None


# ---------- Бот ----------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Это бот для задач.\n\n"
        "Просто напиши текст задачи — я определю её сложность с помощью нейросети и сохраню.\n"
        "Или нажми одну из кнопок, чтобы посмотреть задачи по длительности."
    )
    await message.answer(text, reply_markup=main_keyboard())


# Обработка кнопок фильтрации задач
@dp.message(F.text.in_(list(CATEGORY_LABELS.values())))
async def handle_filter_buttons(message: Message) -> None:
    user_id = message.from_user.id
    btn_text = message.text

    category = category_from_button(btn_text)
    if category is None:
        await message.answer("Не удалось определить категорию для этой кнопки.")
        return

    tasks = get_tasks_by_category(user_id=user_id, category=category)

    if not tasks:
        await message.answer("Задач в этой категории пока нет.", reply_markup=main_keyboard())
        return

    lines = [f"Задачи: {CATEGORY_LABELS[category]}"]
    for t in tasks:
        # Показываем id, чтобы в будущем можно было помечать/удалять
        lines.append(f"{t.id}. {t.description}")

    await message.answer("\n".join(lines), reply_markup=main_keyboard())


# Любой другой текст — это новая задача
@dp.message()
async def handle_new_task(message: Message) -> None:
    user_id = message.from_user.id
    description = message.text.strip()

    if not description:
        await message.answer(
            "Пустое сообщение не похоже на задачу. Напиши, что нужно сделать.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("Думаю над задачей, определяю длительность...")

    # Классифицируем задачу через OpenRouter (GPT-3.5 Turbo)
    category = await classify_task(description)

    # Сохраняем в БД
    task = create_task(user_id=user_id, description=description, category=category)

    human_label = CATEGORY_LABELS.get(category, "Неизвестная категория")

    await message.answer(
        f"Записал задачу:\n"
        f"ID: {task.id}\n"
        f"Текст: {task.description}\n"
        f"Категория: {human_label}",
        reply_markup=main_keyboard(),
    )


async def main() -> None:
    init_db()
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
