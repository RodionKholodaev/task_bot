from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import (
    new_main_keyboard,
    profile_keyboard, 
    duration_category_keyboard,
    purchase_category_keyboard, 
    TASK_CATEGORY_MAP, 
    READABLE_CATEGORIES, 
    task_inline, 
    shopping_inline, 
    PURCHASE_CATEGORY_MAP
    )


from models import Task, ShoppingItem
from services.ai_service import AiService

from services.parser import Parser
from services.message_service import MessageService
from services.formater import Formater
from services.task_service import TaskService
from services.shopping_service import ShoppingService
from typing import List
from db.user_repository import UserRepository

router = Router()

import logging
logger = logging.getLogger(__name__)

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

class ProfileState(StatesGroup):
    waiting_for_description = State()

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
        reply_markup=new_main_keyboard(),
        parse_mode="Markdown"
    )


@router.message(F.text == "⏱ По длительности")
async def by_duration(message: Message):
    """Показать меню выбора по длительности"""
    await message.answer("Выбери категорию:", reply_markup=duration_category_keyboard())

@router.message(F.text == "🧑 Профиль")
async def profile(message: Message):
    """Показать профиль"""
    await message.answer("Профиль", reply_markup=profile_keyboard())


@router.message(F.text == "⬅️ Назад")
async def back(message: Message):
    """Вернуться в главное меню"""
    await message.answer("Главное меню", reply_markup=new_main_keyboard())



@router.message(F.text.in_(TASK_CATEGORY_MAP))
async def show_task_by_category(message: Message):
    """Показать задачи по выбранной категории"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")
    
    tasks = TaskService.get_category_task(user_id, message.text) # type: ignore

    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:

        answer = Formater.format_short_task(t, is_day=False)

        await message.answer(
            answer,
            reply_markup=task_inline(t.id) # type: ignore
        )


@router.message(F.text.in_(PURCHASE_CATEGORY_MAP))
async def show_item_by_category(message: Message):
    """Показать покупки по выбранной категории"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    items = ShoppingService.get_category_item(user_id, message.text) # type: ignore

    if not items:
        await message.answer("Покупок нет")
        return

    for i in items:

        answer = Formater.format_category_item(i)

        await message.answer(
            answer,
            reply_markup=shopping_inline(i.id), # type: ignore
            parse_mode="Markdown"
        )

#  вывод задач на день (вспомогательная функция)
async def show_tasks_for_day(message: Message, day_shift: int):

    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = TaskService.get_day_tasks(user_id, day_shift)

    if not tasks:
        await message.answer("Задач нет 🎉")
        return

    for t in tasks:

        answer = Formater.format_short_task(t, is_day = True)

        await message.answer(
            answer,
            reply_markup=task_inline(t.id) # type: ignore
        )

@router.message(F.text == "📅 Сегодня")
async def today(message: Message):
    await show_tasks_for_day(message, day_shift=0)


@router.message(F.text == "🌅 Завтра")
async def tomorrow(message: Message):
    await show_tasks_for_day(message, day_shift=1)

@router.message(F.text == "📆 Неделя")
async def week(message: Message):
    """Показать задачи на неделю"""

    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = TaskService.get_week_task(user_id)
    if not tasks:
        await message.answer("На неделю задач нет 🎉")
        return

    for t in tasks:

        answer = Formater.format_short_task(t, is_day = False)
        
        await message.answer(
            answer,
            reply_markup=task_inline(t.id) # type: ignore
        )



@router.message(F.text == "📋 Все задачи")
async def all_tasks(message: Message):
    """Показать все задачи"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = TaskService.get_all_tasks(user_id)
    if not tasks:
        await message.answer("Задач нет")
        return

    for t in tasks:

        answer = Formater.format_short_task(t, is_day = False)
        
        await message.answer(
            answer,
            reply_markup=task_inline(t.id) # type: ignore
            )
        
@router.message(F.text == "🛒 Покупки")
async def purchase(message: Message):
    await message.answer("Выбери категорию:", reply_markup=purchase_category_keyboard())



@router.message(F.text == "⏰ Настройка уведомлений")
async def settings(message: Message):

    """Показать инструкции по настройкам"""
    await message.answer(
        "Отправь настройки в формате:\nUTC_OFFSET HH:MM\n\nПример:\n+3 09:00"
    )


# @router.message(F.text == "📝 О себе")
# async def self_description(message: Message, state: FSMContext):
#     """ввод описания себя"""

#     await state.set_state(ProfileState.waiting_for_description)

#     await message.answer(
#         "Укажи то, чем нужно руководствоваться при анализе твоих задач.\n"
#         "Любая информация о тебе, которая может помочь сделать ответы чётче"
#     )

# @router.message(ProfileState.waiting_for_description)
# async def save_description(message: Message, state: FSMContext):

#     description = message.text
#     user_id = message.from_user.id

#     # запись в БД
#     await UserService.update_description(
#         user_id=user_id,
#         description=description
#     )

#     await message.answer("Описание сохранено ✅")

#     await state.clear()

@router.message(F.text.regexp(r"^[+-]?\d+\s\d{2}:\d{2}$"))
async def save_settings(message: Message):
    """Сохранить пользовательские настройки"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    offset_str, time_str = message.text.split() # type: ignore
    UserRepository.upsert_user_settings(
        user_id,
        int(offset_str),
        datetime.strptime(time_str, "%H:%M").time()
    )
    await message.answer("Настройки сохранены ✅", reply_markup=new_main_keyboard())



@router.message(F.reply_to_message)
async def handle_reply(message: Message):
    """
    Обработчик для ответов на сообщения бота, чтобы редактировать задачи и покупки.
    """
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    dt_string = Formater.get_user_time(user_id)

    if not dt_string:
        await message.answer("Часовой пояс не найден, добавьте его в настройках")
        return

    if message.reply_to_message is not None:
        entity_text = message.reply_to_message.text
    else: raise ValueError("нет текста в сообщении")


    id_type = Parser.get_id_info(entity_text)

    type = id_type["type"]
    id = id_type["id"]
    request = message.text

    if request is None:
        await message.answer("введите текст для редактирования")
        return

    description = Formater.make_description(id, type, dt_string,request)
    if description is None: raise ValueError("почему-то не получилось создать описание")

    result = await AiService.ai_edit(description, dt_string, user_id)

# ------------------------- 
    # удаляем старую сущность (задачи или покупка)
    MessageService.delete_entity(id, type, user_id)
    # сохраняем новую(ые) сущность(и)
    entities = MessageService.make_save_new_entity(result, user_id)


    if entities is None:

        await message.answer("Какая-то ошибка. попробуйте отредактировать еще раз")
        raise ValueError("Не получилось создать и сохранить сушность")

    if type =="tasks":

        logger.info("попал в отправку задачи")
        for entity in entities:
            logger.info("попал в цикл отправки задач")
            response_text = Formater.format_task(entity, make_task = False)
            await message.answer(
                response_text,
                reply_markup=task_inline(entity.id),  # type: ignore
                parse_mode="Markdown"
            )
    elif type =="shopping_list":
        for entity in entities:
            response_text = Formater.format_shopping_list(entity)
            await message.answer(
                response_text,
                reply_markup=shopping_inline(entity.id), # type: ignore
                parse_mode="Markdown"
            )


    try:
        await message.reply_to_message.delete()
    except:
        print(f"не удалось удалить сообщение c id = {id}")

    

# --------------------------

@router.message()
async def new_task(message: Message):
    """Обработчик добавления новой задачи"""
    logger.debug(f"поступило сообщение {message.text}")
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    if message.text is None:
        await message.answer("введите текст")
        return

    dt_string = Formater.get_user_time(user_id)

    if not dt_string:
        await message.answer("Часовой пояс не найден, добавьте его в настройках")
        return

    # проверка на длину (500 слов)
    MAX_TEXT_LENGTH = 6*500
    if len(message.text) > MAX_TEXT_LENGTH:
        await message.answer("Слишком длинный текст")
        return
    

    logger.debug(f"передаю в функцию c LLM время и дату: {dt_string}")
    print("до обращения к нейросети в хендлере")
    data_message = await AiService.ai_parse(f"сегодня {dt_string}, {message.text}", user_id)
    print("после")

    if isinstance(data_message, str):
        await message.answer(f"какая-то ошибка с нейросетью. Текст ошибки {data_message}")
        return

    
    data_list = data_message.get("items")
    if not data_list:
        await message.answer("Не получилось выделить задачу из вашего текста. Пожалуйста напишите подробнее")
        return
    print("до сохранения объекта")
    entitys = MessageService.make_save_new_entity(data_message, user_id)
    if entitys is None:
        raise ValueError("ошибка при сохранении сущности")

    if data_message["type"]=="tasks":
            for entity in entitys:
                response_text = Formater.format_task(entity, make_task = True)

                await message.answer(
                    response_text,
                    reply_markup=task_inline(entity.id), # type: ignore
                    parse_mode="Markdown"
                )

    elif data_message["type"]=="shopping_list":
            for entity in entitys:
                response_text = Formater.format_shopping_list(entity)

                await message.answer(
                    response_text,
                    reply_markup=shopping_inline(entity.id), # type: ignore
                    parse_mode="Markdown"
                )
