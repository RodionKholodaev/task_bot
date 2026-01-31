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
    InlineKeyboardMarkup,
    CallbackQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Time
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from ai_client import classify_task  # функция работы с OpenRouter

# ---------- Конфиг ----------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")

DB_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db")

# ---------- БД ----------

# создали класс для всех таблиц в бд
Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)  # short_5, short_30, short_120, long
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deadline_day = Column(Date, nullable=True, index=True)   # Только дата (гггг-мм-дд)
    deadline_time = Column(Time, nullable=True)             # Только время (чч:мм:сс)


engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

# создание строки задачи в бд по полному описанию
def create_task(user_id: int, description: str, category: str) -> Task:
    session: Session = SessionLocal() # подключились в бд
    try:
        task = Task( # создали новую задачу для добавления
            user_id=user_id,
            description=description,
            category=category,
            is_completed=False,
        )
        session.add(task)
        session.commit()
        session.refresh(task) # забираем в task id, который присвоила бд
        return task
    finally:
        session.close() # отключились от бд

# получение задач по категории и пользователю
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

# обозначение задачи выполненой 
def mark_task_completed(task_id: int, user_id: int) -> bool:
    session: Session = SessionLocal()
    try:
        task = (
            session.query(Task)
            .filter(
                Task.id == task_id,
                Task.user_id == user_id,
            )
            .first()
        )
        if not task:
            return False
        task.is_completed = True
        session.commit()
        return True
    finally:
        session.close()

# удаление задачи
def delete_task(task_id: int, user_id: int) -> bool:
    session: Session = SessionLocal()
    try:
        task = (
            session.query(Task)
            .filter(
                Task.id == task_id,
                Task.user_id == user_id,
            )
            .first()
        )
        if not task:
            return False
        session.delete(task)
        session.commit()
        return True
    finally:
        session.close()


# ---------- Клавиатуры ----------
# главная клавиатура
def main_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с фильтрами задач (reply-кнопки).
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

# кнопка под задачей
def task_inline_kb(task_id: int) -> InlineKeyboardMarkup:
    """
    Инлайн‑клавиатура под конкретной задачей.
    Сейчас только кнопка удаления, при желании можно добавить "✅ Готово".
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🗑 Удалить",
        callback_data=f"delete_task:{task_id}",
    )
    builder.adjust(1)
    return builder.as_markup()


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


# срабатывает на команду /start
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

    # Заголовок
    await message.answer(
        f"Задачи: {CATEGORY_LABELS[category]}",
        reply_markup=main_keyboard(),
    )

    # Каждую задачу отправляем отдельным сообщением с инлайн‑кнопкой удаления
    for t in tasks:
        text = f"{t.id}. {t.description}"
        await message.answer(
            text,
            reply_markup=task_inline_kb(task_id=t.id),
        )


# Любой другой текст — это новая задача
@dp.message()
async def handle_new_task(message: Message) -> None:
    user_id = message.from_user.id
    description = message.text.strip() # удаляем ненужные пробелы и переходы на новые строки

    if not description:
        await message.answer(
            "Пустое сообщение не похоже на задачу. Напиши, что нужно сделать.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("Думаю над задачей, определяю длительность...")

    # Классифицируем задачу через OpenRouter
    category = await classify_task(description)

    # Сохраняем в БД
    task = create_task(user_id=user_id, description=description, category=category)

    human_label = CATEGORY_LABELS.get(category, "Неизвестная категория")

    await message.answer(
        f"Записал задачу:\n"
        f"ID: {task.id}\n"
        f"Текст: {task.description}\n"
        f"Категория: {human_label}",
        reply_markup=task_inline_kb(task_id=task.id),
    )


# ---------- CallbackQuery хендлеры ----------

@dp.callback_query(F.data.startswith("delete_task:"))
async def handle_delete_task_callback(callback: CallbackQuery) -> None:
    """
    Удаление задачи по нажатию на инлайн-кнопку.
    Удаляем запись в БД и сообщение в чате.
    """
    user_id = callback.from_user.id
    data = callback.data  # вида "delete_task:123"
    _, task_id_str = data.split(":") # пометили что первый элемент мусорный
    task_id = int(task_id_str)

    ok = delete_task(task_id=task_id, user_id=user_id)
    if not ok:
        await callback.answer("Задача не найдена или уже удалена.", show_alert=True)
        # Можно убрать кнопки, чтобы не мешали
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    # Удаляем сообщение с задачей из чата
    try:
        await callback.message.delete()
    except Exception:
        # Если удалить нельзя (редко, но бывает), просто изменим текст
        try:
            await callback.message.edit_text("Задача удалена.")
        except Exception:
            pass

    await callback.answer("Задача удалена ✅")


# ---------- Точка входа ----------

async def main() -> None:
    init_db()
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
