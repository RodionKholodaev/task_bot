# список дел:
#TODO настроить логирование
#TODO настроить обработку отключения api ключа
#TODO более удобный ввод настроек
#TODO сделать так чтобы при выводе задачи выводилась и время и дата если они есть
#TODO расставить коментарии


import asyncio
import os
from datetime import datetime, timedelta, date, time, timezone
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
    Time,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from ai_client import classify_task

# ================= CONFIG =================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

Base = declarative_base() # класс бд
engine = create_engine(DB_URL, echo=False) # то что дает пойтону подключится к бд
SessionLocal = sessionmaker(bind=engine) # фабрика сессий 

# модель для задачи
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    deadline_day = Column(Date, nullable=True)
    deadline_time = Column(Time, nullable=True)

# модель пользователя
class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, primary_key=True)
    utc_offset = Column(Integer, nullable=False)
    notify_time = Column(Time, nullable=False)

# создание таблиц, если нужно при запуске
def init_db():
    Base.metadata.create_all(bind=engine)


# ================= DB HELPERS =================
# побращение к сессии TODO нужно убрать
def get_session() -> Session:
    return SessionLocal()

# получение данные о пользоваетеле TODO нужно сделать через with
def get_user_settings(user_id: int) -> UserSettings | None:
    s = get_session()
    try:
        return s.query(UserSettings).filter_by(user_id=user_id).first()
    finally:
        s.close()

# обносление настроек пользователя
def upsert_user_settings(user_id: int, utc_offset: int, notify_time: time):
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

# сохранение задачи
def save_task(task: Task):
    s = get_session()
    try:
        s.add(task)
        s.commit()
        s.refresh(task)
        return task
    finally:
        s.close()

# получение задач на сегодня
def get_tasks_today(user_id: int, day: date) -> List[Task]:
    s = get_session()
    try:
        return s.query(Task).filter(
            Task.user_id == user_id,
            Task.deadline_day == day,
            Task.is_completed == False
        ).order_by(Task.deadline_time).all()
    finally:
        s.close()

# получение задач на неделю
def get_tasks_week(user_id: int, start: date, end: date) -> List[Task]:
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
# получение даты в часовом поясе пользователя
def get_user_date(utc_offset: int) -> str:
    user_tz = timezone(timedelta(hours=utc_offset))
    user_datetime = datetime.now(user_tz)
    return user_datetime.strftime("%Y-%m-%d")

# получение всех задач
def get_all_tasks(user_id: int) -> List[Task]:
    s = get_session()
    try:
        return s.query(Task).filter(Task.user_id == user_id).all()
    finally:
        s.close()

# пометка задачи выполненой
def mark_done(task_id: int, user_id: int) -> bool:
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

# удаление задачи
def delete_task(task_id: int, user_id: int) -> bool:
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


# ================= KEYBOARDS =================
# главное меню
def main_keyboard():
    # возвращаем ответное меню
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📆 Неделя")],
            [KeyboardButton(text="📋 Все задачи")],
            [KeyboardButton(text="⏱ По длительности")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True, # расмер кнопок подстраивается под размер текста в них
    )


def category_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="≤ 5 минут"), KeyboardButton(text="≤ 30 минут")],
            [KeyboardButton(text="≤ 2 часов"), KeyboardButton(text="Сложные задачи")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


CATEGORY_MAP = {
    "≤ 5 минут": "short_5",
    "≤ 30 минут": "short_30",
    "≤ 2 часов": "short_120",
    "Сложные задачи": "long",
}

# кнопки, которые прилипает к сообщению
def task_inline(task_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Выполнено", callback_data=f"done:{task_id}")
    kb.button(text="🗑 Удалить", callback_data=f"delete:{task_id}")
    kb.adjust(2) # в отдной строке 2 кнопки
    return kb.as_markup() # возвращаем собранную встроенную клавиатуру


# ================= HANDLERS =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
    "Привет! 👋 Я твой умный менеджер задач.\n\n"
            "**Что я умею:**\n"
            "🤖 **Понимаю свободный текст** — просто напиши «Купить хлеб в 18:00», и я сам создам задачу с датой.\n"
            "🔔 **Напоминаю о делах** — пришлю список задач на день в удобное для тебя время.\n"
            "⏳ **Сортирую по времени** — помогу найти быстрые пятиминутки или сложные дела.\n"
            "📅 **Планирую** — покажу задачи на сегодня, неделю или всё сразу.\n\n"
            "Настрой свой часовой пояс в настройках, чтобы уведомления приходили вовремя!",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(F.text == "⏱ По длительности") # свзязывает нажатие кнопи с функцией
async def by_duration(message: Message):
    await message.answer("Выбери категорию:", reply_markup=category_keyboard()) # переход к новому меню


@dp.message(F.text == "⬅️ Назад") # свзязывает нажатие кнопи с функцией
async def back(message: Message):
    await message.answer("Главное меню", reply_markup=main_keyboard()) # возврат к старому меню


@dp.message(F.text.in_(CATEGORY_MAP))
async def show_by_category(message: Message):
    user_id = message.from_user.id
    category = CATEGORY_MAP[message.text]

    s = get_session()
    try:
        tasks = s.query(Task).filter(
            Task.user_id == user_id,
            Task.category == category,
            Task.is_completed == False
        ).all()
    finally:
        s.close()

    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:
        await message.answer(t.description, reply_markup=task_inline(t.id))


@dp.message(F.text == "📅 Сегодня")
async def today(message: Message):
    settings = get_user_settings(message.from_user.id)
    offset = settings.utc_offset if settings else 0
    today = (datetime.utcnow() + timedelta(hours=offset)).date()

    tasks = get_tasks_today(message.from_user.id, today)
    if not tasks:
        await message.answer("Сегодня задач нет 🎉")
        return

    for t in tasks:
        await message.answer(t.description, reply_markup=task_inline(t.id))


@dp.message(F.text == "📆 Неделя")
async def week(message: Message):
    settings = get_user_settings(message.from_user.id)
    offset = settings.utc_offset if settings else 0

    start = (datetime.utcnow() + timedelta(hours=offset)).date()
    end = start + timedelta(days=7)

    tasks = get_tasks_week(message.from_user.id, start, end)
    if not tasks:
        await message.answer("На неделю задач нет 🎉")
        return

    for t in tasks:
        await message.answer(
            f"{t.deadline_day}: {t.description}",
            reply_markup=task_inline(t.id)
        )


@dp.message(F.text == "📋 Все задачи")
async def all_tasks(message: Message):
    tasks = get_all_tasks(message.from_user.id)
    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:
        status = "✅" if t.is_completed else "⏳"
        await message.answer(f"{status} {t.description}", reply_markup=task_inline(t.id))


@dp.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    await message.answer(
        "Отправь настройки в формате:\nUTC_OFFSET HH:MM\n\nПример:\n+3 09:00"
    )


@dp.message(F.text.regexp(r"^[+-]?\d+\s\d{2}:\d{2}$"))
async def save_settings(message: Message):
    offset_str, time_str = message.text.split()
    upsert_user_settings(
        message.from_user.id,
        int(offset_str),
        datetime.strptime(time_str, "%H:%M").time()
    )
    await message.answer("Настройки сохранены ✅", reply_markup=main_keyboard())


@dp.message()
async def new_task(message: Message):
    settings = get_user_settings(message.from_user.id)
    if not settings:
        await message.answer("Не найден часовой пояс пользователя")
        return

    user_date = get_user_date(settings.utc_offset)

    data = await classify_task(
        f"сегодня {user_date}, {message.text}"
    )

    # Безопасное извлечение даты и времени
    try:
        deadline_day = datetime.strptime(data["date"], "%Y-%m-%d").date() if data.get("date") else None
    except (ValueError, TypeError):
        deadline_day = None

    try:
        # Проверяем, не пустая ли строка времени
        time_str = data.get("time")
        deadline_time = datetime.strptime(time_str, "%H:%M").time() if time_str else None
    except (ValueError, TypeError):
        deadline_time = None

    # Создаем объект задачи
    task = Task(
        user_id=message.from_user.id,
        description=data.get("task", message.text), # если ИИ не вернул текст, берем текст сообщения
        category=data.get("category", "short_30"),
        deadline_day=deadline_day,
        deadline_time=deadline_time,
    )

    # Сохраняем в БД
    save_task(task)

    # --- ФОРМИРУЕМ КРАСИВЫЙ ОТВЕТ ---
    
    # Маппинг категорий для пользователя
    readable_categories = {
        "short_5": "⚡️ До 5 минут",
        "short_30": "⏳ До 30 минут",
        "short_120": "🕒 До 2 часов",
        "long": "🐘 Сложная/долгая"
    }
    
    cat_text = readable_categories.get(task.category, task.category)
    date_text = task.deadline_day 
    time_text = task.deadline_time

    response_text = (
        f"✅ **Задача добавлена!**\n\n"
        f"📝 **Что:** {task.description}\n"
        f"📁 **Категория:** {cat_text}\n"
        f"📅 **Дата:** {date_text}\n"
        f"⏰ **Время:** {time_text}"
    )

    await message.answer(
        # Используем parse_mode="Markdown" для жирного шрифта
        response_text, 
        reply_markup=task_inline(task.id),
        parse_mode="Markdown"
    )


# ================= CALLBACKS =================

@dp.callback_query(F.data.startswith("done:"))
async def done(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    if mark_done(task_id, callback.from_user.id):
        await callback.message.edit_text("✅ Выполнено")
    await callback.answer()


@dp.callback_query(F.data.startswith("delete:"))
async def delete(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    if delete_task(task_id, callback.from_user.id):
        await callback.message.delete()
    await callback.answer()


# ================= NOTIFICATIONS =================

async def notification_loop():
    while True:
        now = datetime.utcnow()

        s = get_session()
        try:
            users = s.query(UserSettings).all()
        finally:
            s.close()

        for u in users:
            local = now + timedelta(hours=u.utc_offset)
            if (
                local.hour == u.notify_time.hour and
                local.minute == u.notify_time.minute
            ):
                tasks = get_tasks_today(u.user_id, local.date())
                if tasks:
                    text = "🔔 Задачи на сегодня:\n" + "\n".join(
                        f"- {t.description}" for t in tasks
                    )
                    await bot.send_message(u.user_id, text)

        await asyncio.sleep(60)


# ================= ENTRY =================

async def main():
    init_db()
    asyncio.create_task(notification_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
