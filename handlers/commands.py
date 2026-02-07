from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_keyboard, category_keyboard, CATEGORY_MAP, READABLE_CATEGORIES, task_inline
from database import get_user_settings, get_tasks_today, get_tasks_week, get_all_tasks, get_tasks_by_category, upsert_user_settings
from models import Task
from ai_client import classify_task
from database import save_task

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! 👋 Я твой умный менеджер задач.\n\n"
        "**Что я умею:**\n"
        "🤖 **Понимаю свободный текст** — просто напиши «Купить хлеб в 18:00», и я сам создам задачу с датой.\n"
        "🔔 **Напоминаю о делах** — пришлю список задач на день и напомню о любой задачи в удобное для тебя время.\n"
        "⏳ **Сортирую по времени** — помогу найти быстрые пятиминутки или сложные дела.\n"
        "📅 **Планирую** — покажу задачи на сегодня, неделю или всё сразу.\n\n"
        "Настрой свой часовой пояс в настройках, чтобы уведомления приходили вовремя!",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )


@router.message(F.text == "⏱ По длительности")
async def by_duration(message: Message):
    """Показать меню выбора по длительности"""
    await message.answer("Выбери категорию:", reply_markup=category_keyboard())


@router.message(F.text == "⬅️ Назад")
async def back(message: Message):
    """Вернуться в главное меню"""
    await message.answer("Главное меню", reply_markup=main_keyboard())


@router.message(F.text.in_(CATEGORY_MAP))
async def show_by_category(message: Message):
    """Показать задачи по выбранной категории"""
    from database import get_session
    
    user_id = message.from_user.id
    category = CATEGORY_MAP[message.text]

    tasks = get_tasks_by_category(user_id, category)

    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:
        await message.answer(
            f" {t.deadline_day.strftime("%d-%m-%Y") if t.deadline_day else ""} {t.description}",
            reply_markup=task_inline(t.id)
        )


@router.message(F.text == "📅 Сегодня")
async def today(message: Message):
    """Показать задачи на сегодня"""
    settings = get_user_settings(message.from_user.id)
    offset = settings.utc_offset if settings else 0
    today = (datetime.utcnow() + timedelta(hours=offset)).date()

    tasks = get_tasks_today(message.from_user.id, today)
    if not tasks:
        await message.answer("Сегодня задач нет 🎉")
        return

    for t in tasks:
        deadlinne_time=t.deadline_time if t.deadline_time else ""
        await message.answer(f"{deadlinne_time} {t.description}", reply_markup=task_inline(t.id))


@router.message(F.text == "📆 Неделя")
async def week(message: Message):
    """Показать задачи на неделю"""
    settings = get_user_settings(message.from_user.id)
    offset = settings.utc_offset if settings else 0

    start = (datetime.utcnow() + timedelta(hours=offset)).date()
    end = start + timedelta(days=7)

    tasks = get_tasks_week(message.from_user.id, start, end)
    if not tasks:
        await message.answer("На неделю задач нет 🎉")
        return

    for t in tasks:
        deadlinne_time=t.deadline_time if t.deadline_time else ""
        await message.answer(
            f"{t.deadline_day.strftime("%d-%m-%Y")} {deadlinne_time}: {t.description}",
            reply_markup=task_inline(t.id)
        )


@router.message(F.text == "📋 Все задачи")
async def all_tasks(message: Message):
    """Показать все задачи"""
    tasks = get_all_tasks(message.from_user.id)
    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:
        status = "✅" if t.is_completed else "⏳"
        deadline = t.deadline_day.strftime("%d-%m-%Y") if t.deadline_day else ""
        await message.answer(f"{status} {deadline} {t.description}", reply_markup=task_inline(t.id))


@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    """Показать инструкции по настройкам"""
    await message.answer(
        "Отправь настройки в формате:\nUTC_OFFSET HH:MM\n\nПример:\n+3 09:00"
    )


@router.message(F.text.regexp(r"^[+-]?\d+\s\d{2}:\d{2}$"))
async def save_settings(message: Message):
    """Сохранить пользовательские настройки"""
    
    offset_str, time_str = message.text.split()
    upsert_user_settings(
        message.from_user.id,
        int(offset_str),
        datetime.strptime(time_str, "%H:%M").time()
    )
    await message.answer("Настройки сохранены ✅", reply_markup=main_keyboard())


@router.message()
async def new_task(message: Message):
    """Обработчик добавления новой задачи"""
    settings = get_user_settings(message.from_user.id)
    if not settings:
        await message.answer("Не найден часовой пояс пользователя")
        return

    # Получаем дату в часовом поясе пользователя
    user_tz = timezone(timedelta(hours=settings.utc_offset))
    user_datetime = datetime.now(user_tz)
    dt_string = user_datetime.strftime("%Y-%m-%d %H:%M")

    # Классифицируем задачу с помощью ИИ
    data_list = await classify_task(f"сегодня {dt_string}, {message.text}")

    if isinstance(data_list, str):
        if "Error code" in data_list:
            print(data_list)
            await message.answer(f"какая-то ошибка с нейросетью. Текст ошибки {data_list}")
            return
        else:
            await message.answer(data_list)
    for data in data_list:

        # Безопасное извлечение даты и времени
        try:
            deadline_day = datetime.strptime(data["date"], "%Y-%m-%d").date() if data.get("date") else None
        except (ValueError, TypeError):
            deadline_day = None

        try:
            time_str = data.get("time")
            deadline_time = datetime.strptime(time_str, "%H:%M").time() if time_str else None
        except (ValueError, TypeError):
            deadline_time = None
        
        try:
            print("начал работать с remind_date")
            remind_date_str=data.get("remind_date")
            remind_date=datetime.strptime(remind_date_str, "%Y-%m-%d").date() if remind_date_str else None
            print(remind_date)
        except Exception as e:
            print(f"попал в exception в remind_date, ошибка: {e}")
            remind_date=None

        try:
            remind_time_str=data.get("remind_time")
            remind_time=datetime.strptime(remind_time_str, "%H:%M").time() if remind_time_str else None
        except:
            remind_time=None

        # Создаем объект задачи
        task = Task(
            user_id=message.from_user.id,
            description=data.get("task", message.text),
            category=data.get("category", "short_30"),
            deadline_day=deadline_day,
            deadline_time=deadline_time,
            remind_time=remind_time,
            remind_date=remind_date
        )

        # Сохраняем в БД
        save_task(task)

        # Формируем красивый ответ
        cat_text = READABLE_CATEGORIES.get(task.category, task.category)
        date_text = task.deadline_day.strftime("%d-%m-%Y") if task.deadline_day else None
        time = task.deadline_time.strftime("%H:%M") if task.deadline_time else None
        remind_date_str=task.remind_date.strftime("%d-%m-%Y") if task.remind_date else None
        remind_time = task.remind_time.strftime("%H:%M") if task.remind_time else None


        response_text = (
            f"✅ **Задача добавлена!**\n\n"
            f"📝 **Что:** {task.description}\n"
            f"📁 **Категория:** {cat_text}\n"
            f"📅 **Дата:** {date_text}\n"
            f"⏰ **Время:** {time}\n"
            f"🚨 **Напоминание дата:** {remind_date_str}\n"
            f"⏱️ **Напоминание время:** {remind_time}"
        )

        await message.answer(
            response_text,
            reply_markup=task_inline(task.id),
            parse_mode="Markdown"
        )
