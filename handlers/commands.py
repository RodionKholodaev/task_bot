from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import (
    main_keyboard, 
    duration_category_keyboard,
    purchase_category_keyboard, 
    TASK_CATEGORY_MAP, 
    READABLE_CATEGORIES, 
    task_inline, 
    shopping_inline, 
    PURCHASE_CATEGORY_MAP
    )

from database import (
    get_user_settings, 
    get_tasks_today, 
    get_tasks_week, 
    get_all_tasks, 
    get_tasks_by_category, 
    get_item_by_category,
    upsert_user_settings, 
    get_task_by_id,
    delete_task,
    save_task,
    save_shopping_item
    )

from models import Task, ShoppingItem
from ai_client import parse_text, edit_task

from services.parser import Parser
from services.message_service import MessageService
from services.formater import Formater

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! 👋 Я твой умный личный менеджер.\n\n"
        "**Что я умею:**\n\n"
        "🤖 **Понимаю свободный текст** — просто напиши «Купить хлеб в 18:00» или «Созвон в пятницу», и я сам создам задачу или добавлю покупку.\n\n"
        "🔔 **Напоминаю о делах** — пришлю список задач на день и напомню о любой задаче в удобное для тебя время.\n\n"
        "🛒 **Веду список покупок** — сохраняю покупки, группирую их по категориям и показываю всё в удобном виде.\n\n"
        "⏳ **Сортирую по времени** — помогу найти быстрые пятиминутки или важные и сложные дела.\n\n"
        "📅 **Планирую** — покажу задачи на сегодня, неделю или весь список сразу.\n\n"
        "✏️ **Редактирую ответом** — чтобы изменить или посмотреть задачу или покупку, просто свайпни её сообщение влево и напиши, что поправить!\n\n"
        "Настрой свой часовой пояс в настройках, чтобы уведомления приходили вовремя!",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )


@router.message(F.text == "⏱ По длительности")
async def by_duration(message: Message):
    """Показать меню выбора по длительности"""
    await message.answer("Выбери категорию:", reply_markup=duration_category_keyboard())


@router.message(F.text == "⬅️ Назад")
async def back(message: Message):
    """Вернуться в главное меню"""
    await message.answer("Главное меню", reply_markup=main_keyboard())


@router.message(F.text.in_(TASK_CATEGORY_MAP))
async def show_task_by_category(message: Message):
    """Показать задачи по выбранной категории"""
    
    user_id = message.from_user.id
    category = TASK_CATEGORY_MAP[message.text]

    tasks = get_tasks_by_category(user_id, category)

    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:

        deadline_day = t.deadline_day.strftime('%d-%m-%Y') if t.deadline_day else ''
        deadline_time = t.deadline_time.strftime('%H-%M') if t.deadline_time else ''

        answer = (
            f" {deadline_day} {deadline_time} {t.description}\n"
            f"ID задачи: {t.id}"
            )

        await message.answer(
            answer,
            reply_markup=task_inline(t.id)
        )


@router.message(F.text.in_(PURCHASE_CATEGORY_MAP))
async def show_item_by_category(message: Message):
    """Показать покупки по выбранной категории"""
    
    user_id = message.from_user.id
    category = PURCHASE_CATEGORY_MAP[message.text]

    item = get_item_by_category(user_id, category)

    if not item:
        await message.answer("Покупок нет")
        return

    for i in item:

        answer = Formater.format_category_item(i)

        await message.answer(
            answer,
            reply_markup=shopping_inline(i.id),
            parse_mode="Markdown"
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

        deadlinne_time=t.deadline_time.strftime('%H-%M') if t.deadline_time else ""
        
        answer = (
            f"{deadlinne_time} {t.description}\n"
            f"ID задачи: {t.id}"
            )

        await message.answer(
            answer, 
            reply_markup=task_inline(t.id)
            )



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

        deadline_time=t.deadline_time.strftime('%H-%M') if t.deadline_time else ""
        deadline_day = t.deadline_day.strftime('%d-%m-%Y') if t.deadline_day else ""

        answer = (
            f"{deadline_day} {deadline_time}: {t.description}\n"
            f"ID задачи: {t.id}"
            )
        
        await message.answer(
            answer,
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

        status = "✅" if t.is_completed else "⏳" # вообще всегда будет только "⏳", но вдруг это пригодится

        deadline = t.deadline_day.strftime("%d-%m-%Y") if t.deadline_day else ""
        deadline_time=t.deadline_time.strftime('%H-%M') if t.deadline_time else ""

        answer = (
            f"{status} {deadline} {deadline_time} {t.description}\n"
            f"ID задачи: {t.id}"
            )
        
        await message.answer(
            answer,
            reply_markup=task_inline(t.id)
            )
        
@router.message(F.text == "🛒 Покупки")
async def purchase(message: Message):
    await message.answer("Выбери категорию:", reply_markup=purchase_category_keyboard())



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



@router.message(F.reply_to_message)
async def handle_reply(message: Message):
    """
    Обработчик для ответов на сообщения бота, чтобы редактировать задачи.
    """
    if message.reply_to_message:
        user_id = message.from_user.id
        dt_string = Parser.get_user_time(user_id)

        if not dt_string:
            await message.answer("Часовой пояс не найден, добавьте его в настройках")

        user_id = message.from_user.id
        task_text = message.reply_to_message.text

        task_id = MessageService.extract_task_id(task_text)

        task = get_task_by_id(task_id)

        if not task:
            await message.answer("Не удалось найти задачу для редактирования.")
            return


        information = {
            "request": message.text,
            "category": task.category,
            "date": task.deadline_day,
            "time": task.deadline_time,
            "remind_date": task.remind_date,
            "remind_time": task.remind_time,
            "task": task.description
            }

        result = await edit_task(information, dt_string)
# ------------------------
#   НЕТ ПРОВЕРКИ НА БРЕД СО СТОРОНЫ НЕЙРОСЕТИ (видимо нужно использовать pydentic)
        # отправка сообщения в случае если пользователь отправит какой-то бред
        if result["type"] == "chat":
            await message.answer(result["message"])
            return

# ------------------------- 
        # удаляем старую задачу

        delete_task(task_id, user_id)

        # Создаем объект задачи

        data = result["items"][0]

        data_time = Parser.parse_date(data)

        task = Task(
            user_id=message.from_user.id,
            description=data.get("task", message.text),
            category=data.get("category", "short_30"),
            deadline_day=data_time["date"],
            deadline_time=data_time["time"],
            remind_time=data_time["remind_time"],
            remind_date=data_time["remind_date"]
        )

        # Сохраняем в БД
        save_task(task)

        response_text = Formater.format_task(task, make_task = False)

        await message.answer(
            response_text,
            reply_markup=task_inline(task.id),
            parse_mode="Markdown"
        )

        try:
            await message.reply_to_message.delete()
        except:
            print(f"не удалось удалить сообщение c id = {task_id}")

        

# --------------------------

@router.message()
async def new_task(message: Message):
    """Обработчик добавления новой задачи"""
    print(f"поступило сообщение {message.text}")

    user_id = message.from_user.id
    dt_string = Parser.get_user_time(user_id)

    if not dt_string:
        await message.answer("Часовой пояс не найден, добавьте его в настройках")
        return

    # проверка на длину (500 слов)
    MAX_TEXT_LENGTH = 6*500
    if len(message.text) > MAX_TEXT_LENGTH:
        await message.answer("Слишком длинный текст")
        return
    
    print("иду в функцию обращения к нейронке для класификации задачи")
    print(f"передаю в функцию время и дату {dt_string}")
    data_message = await parse_text(f"сегодня {dt_string}, {message.text}")

    if isinstance(data_message, str):
        print(data_message)
        await message.answer(f"какая-то ошибка с нейросетью. Текст ошибки {data_message}")
        return

    
    data_list = data_message.get("items")

    if data_list == []:
        message.answer("Не получилось выделить задачу из вашего текста. Пожалуйста напишите подробнее")
        return

    if data_message["type"]=="tasks":
        for data in data_list:

            data_time = Parser.parse_date(data)

            # Создаем объект задачи
            task = Task(
                user_id=user_id,
                description=data.get("task", message.text),
                category=data.get("category", "short_30"),
                deadline_day=data_time["date"],
                deadline_time=data_time["time"],
                remind_time=data_time["remind_time"],
                remind_date=data_time["remind_date"]
            )

            # Сохраняем в БД
            save_task(task)

            response_text = Formater.format_task(task, make_task = True)

            await message.answer(
                response_text,
                reply_markup=task_inline(task.id),
                parse_mode="Markdown"
            )

    elif data_message["type"]=="shopping_list":
        for data in data_list:
            amount = Parser.parse_num(data["amount"])
            
            shopping_item = ShoppingItem(
                user_id=user_id,
                item = data["item"],
                category = data["category"],
                amount = amount,
                unit = data["unit"],
                is_bought = False
            )

            item = save_shopping_item(shopping_item)

            response_text = Formater.format_shopping_list(shopping_item)

            await message.answer(
                response_text,
                reply_markup=shopping_inline(item.id), 
                parse_mode="Markdown"
            )
