from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_keyboard, category_keyboard, CATEGORY_MAP, READABLE_CATEGORIES, task_inline
from database import (
    get_user_settings, 
    get_tasks_today, 
    get_tasks_week, 
    get_all_tasks, 
    get_tasks_by_category, 
    upsert_user_settings,
    save_new_message_id,
    get_task_by_message_id
    )
from services.task_service import TaskService

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
    
    user_id = message.from_user.id
    category = CATEGORY_MAP[message.text]

    tasks = get_tasks_by_category(user_id, category)

    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:
        sent_message = await message.answer(
            f" {t.deadline_day.strftime('%d-%m-%Y') if t.deadline_day else ''} {t.description}",
            reply_markup=task_inline(t.id)
        )
        save_new_message_id(sent_message.message_id, t.id, user_id)


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
        sent_message = await message.answer(f"{deadlinne_time} {t.description}", reply_markup=task_inline(t.id))
        save_new_message_id(sent_message.message_id, t.id, t.user_id)


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
        sent_message = await message.answer(
            f"{t.deadline_day.strftime('%d-%m-%Y')} {deadlinne_time}: {t.description}",
            reply_markup=task_inline(t.id)
        )
        save_new_message_id(sent_message.message_id, t.id, t.user_id)


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
        sent_message = await message.answer(f"{status} {deadline} {t.description}", reply_markup=task_inline(t.id))
        save_new_message_id(sent_message.message_id, t.id, t.user_id)

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
async def handle_reply(message: Message):
    """
    Обработчик для ответов на сообщения бота, чтобы редактировать задачи.
    """
    if message.reply_to_message:
        user_id = message.from_user.id
        message_id = message.reply_to_message.message_id
        task = get_task_by_message_id(message_id, user_id)

        if not task:
            await message.answer("Не удалось найти задачу для редактирования.")
            return

        # Обновляем задачу через TaskService
        result = await TaskService.process_task(user_id, message.text, edit=True)

        if "error" in result:
            await message.answer(result["error"])
            return

        if "chat_message" in result:
            await message.answer(result["chat_message"])
            return

        for task_data in result["tasks"]:
            sent_message = await message.answer(
                task_data["response_text"],
                reply_markup=task_inline(task_data["task"].id),
                parse_mode="Markdown"
            )
            save_new_message_id(sent_message.message_id, task_data["task"].id, task_data["task"].user_id)

@router.message()
async def new_task(message: Message):
    """
    Обработчик добавления новой задачи.
    """
    result = TaskService.process_task(message.from_user.id, message.text, edit=False)

    if "error" in result:
        await message.answer(result["error"])
        return

    if "chat_message" in result:
        await message.answer(result["chat_message"])
        return

    for task_data in result["tasks"]:
        sent_message = await message.answer(
            task_data["response_text"],
            reply_markup=task_inline(task_data["task"].id),
            parse_mode="Markdown"
        )
        save_new_message_id(sent_message.message_id, task_data["task"].id, task_data["task"].user_id)
