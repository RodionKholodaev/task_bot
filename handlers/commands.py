from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import (
    new_main_keyboard,
    profile_keyboard, 
    duration_category_keyboard,
    purchase_category_keyboard, 
    TASK_CATEGORY_MAP, 
    task_inline, 
    shopping_inline, 
    PURCHASE_CATEGORY_MAP,
    skip_description_keyboard,
    buy_inline
    )

from services.ai_service import AiService

from services.parser import Parser
from services.message_service import MessageService
from services.formater import Formater
from services.task_service import TaskService
from services.shopping_service import ShoppingService
from services.voice_service import transcribe_voice

from db.user_repository import UserRepository
from db.payments_repository import PaymentsRepository
from db.statistics import Statistics
from sqlalchemy.ext.asyncio import AsyncSession

from models import SubscriptionTypes


router = Router()

import logging
logger = logging.getLogger(__name__)

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# middleware
from middlewares.limits import TaskLimitMiddleware
router.message.middleware(TaskLimitMiddleware())

class ProfileState(StatesGroup):
    waiting_for_description = State()

@router.message(CommandStart())
async def start(message: Message, s: AsyncSession):
    """Обработчик команды /start"""
    if message.from_user is None:
        raise ValueError("У сообщения нет пользователя")
    user_id = message.from_user.id
  
    await PaymentsRepository.get_started(s, user_id)
        
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
    msg = await message.answer(
        "📌 Краткая инструкция\n\n"
        "• Пиши задачи и покупки обычным текстом:\n"
        "→ «Созвон в пятницу в 19, напомни за час», «Купить хлеб, молоко, яйца, 3 пачки творога».\n\n"
        "• Для изменения задачи или покупки ответь на сообщение и укажи изменения.\n\n"
        "• Если у задачи есть дата, я напомню в указанный день (время напоминания укажи в профиле).\n\n"
        "• Все покупки можно посмотреть по категориям в разделе: 🛒 покупки.\n\n"
        "• Задачи доступны по категориям времени (сегодня, завтра, неделя, всё) и по времени выполнения (<5 минут, <30 минут, <2 часов, Сложные задачи).\n\n"
        "• Можешь добавить краткое описание себя в профиле, для того чтобы бот мог точнее определять время на задачи"
        "⚙️ Настрой часовой пояс и время уведомлений в профиле!"
    )

    await msg.pin()


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
async def show_task_by_category(message: Message, s: AsyncSession):
    """Показать задачи по выбранной категории"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = await TaskService.get_category_task(s, user_id, message.text) # type: ignore

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
async def show_item_by_category(message: Message, s: AsyncSession):
    """Показать покупки по выбранной категории"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    items = await ShoppingService.get_category_item(s, user_id, message.text) # type: ignore

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
async def show_tasks_for_day(message: Message,s: AsyncSession, day_shift: int):

    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = await TaskService.get_day_tasks(s, user_id, day_shift)

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
async def today(message: Message, s: AsyncSession):
    await show_tasks_for_day(message, s, day_shift=0)


@router.message(F.text == "🌅 Завтра")
async def tomorrow(message: Message, s: AsyncSession):
    await show_tasks_for_day(message, s, day_shift=1)

@router.message(F.text == "📆 Неделя")
async def week(message: Message, s: AsyncSession):
    """Показать задачи на неделю"""

    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = await TaskService.get_week_task(s, user_id)

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
async def all_tasks(message: Message, s: AsyncSession):
    """Показать все задачи"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    tasks = await TaskService.get_all_tasks(s, user_id)

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


@router.message(F.text == "📝 О себе")
async def self_description(message: Message, state: FSMContext, s: AsyncSession):
    """ввод описания себя"""
    if message.from_user:
        user_id = message.from_user.id
    else:
        raise ValueError("не найден пользователь")
    
    description = UserRepository.get_description(s, user_id)

    if description:
        await message.answer(
            "Ваше текущее описание:"
        )
        await message.answer(
            f"{description}"
        )
        await message.answer(
            "Введите новое описание следующим сообщением"
        )
    else:
        await message.answer("У вас пока нет описания себя")
        
    await state.set_state(ProfileState.waiting_for_description)

    await message.answer(
        "Укажи то, чем нужно руководствоваться при анализе твоих задач.\n"
        "Любая информация о тебе, которая может помочь сделать ответы чётче",
        reply_markup=skip_description_keyboard()
    )

@router.message(ProfileState.waiting_for_description, F.text == "❌ Не вводить")
async def skip_description(message: Message, state: FSMContext):
    await message.answer(
        "Ок, описание не изменено 👍",
        reply_markup=profile_keyboard()
    )

    await state.clear()

@router.message(ProfileState.waiting_for_description)
async def save_description(message: Message, state: FSMContext, s: AsyncSession):
    if message.from_user is None:
        await message.answer("у сообщения нет пользователя")
        return
    
    if message.text is None: 
        await message.answer("в сообщении нет текста")
        return
    
    description = message.text
    user_id = message.from_user.id

    MAX_DESCRIPTION_SIZE = 6*100
    if len(description)> MAX_DESCRIPTION_SIZE:
        await message.answer("Слишком длинное описание. Максимальная длинна 600 символов")
        return
    # запись в БД

    await UserRepository.update_description(
        s,
        user_id=user_id,
        description=description
    )

    await message.answer("Описание сохранено ✅", reply_markup=profile_keyboard())

    await state.clear()



@router.message(F.text == "📊 Статистика")
async def statistic(message: Message):
    if message.from_user is None:
        return # Просто выходим, а не raise, чтобы бот не падал в логах
    
    user_id = message.from_user.id
    
    # --- ПОЛУЧЕНИЕ СЕССИИ ---
    # ЗАМЕНИ ЭТОТ БЛОК НА ТВОЙ СПОСОБ ПОЛУЧЕНИЯ AsyncSession
    # Например, если сессия передается через middleware в state или context
    # async with get_db_session() as session: 
    #    ... код ниже ...
    
    # Для примера предполагаем, что session уже есть или получаем так:
    # session: AsyncSession = await db_manager.get_session() 
    # В реальном проекте лучше использовать dependency injection или middleware
    
    try:
        # Временная заглушка для сессии, удали и используй свою
        from db.database import get_session # Пример импорта твоей фабрики сессий
        async with get_session() as session:
            
            # 1. Собираем все данные параллельно или последовательно
            productivity = await Statistics.get_productivity_score(session, user_id)
            logger.debug(f"получил productivity: {productivity}")
            top_categories = await Statistics.get_top_task_categories(session, user_id)
            logger.debug(f"получил top_categories: {top_categories}")
            shopping = await Statistics.get_shopping_habits(session, user_id)
            logger.debug(f"получил shopping: {shopping}")
            overdue = await Statistics.get_deadline_pressure(session, user_id)
            logger.debug(f"получил overdue: {overdue}")
            account = await Statistics.get_account_info(session, user_id)
            logger.debug(f"получил account: {account}")

            # 2. Формируем текст сообщения
            text = f"📊 <b>Ваша личная статистика</b>\n\n"
            
            # Продуктивность
            color = "🟢" if productivity > 70 else "🟡" if productivity > 40 else "🔴"
            text += f"{color} <b>Эффективность:</b> {productivity}% выполненных задач\n"
            text += f"   <i>(Закрыто дел от общего количества)</i>\n\n"
            
            # Задачи
            text += f"📌 <b>Активность в задачах:</b>\n"
            if top_categories:
                cats_text = ", ".join([f"{cat} ({cnt})" for cat, cnt in top_categories])
                text += f"   Топ категории: {cats_text}\n"
            else:
                text += f"   Пока нет задач\n"
            
            if overdue > 0:
                text += f"   ⚠️ <b>Просрочено:</b> {overdue} задач(и) требуют внимания!\n"
            else:
                text += f"   ✅ Просроченных задач нет\n"
            text += "\n"
            
            # Покупки
            text += f"🛒 <b>Покупки:</b>\n"
            text += f"   Чаще всего покупаете: <b>{shopping['top_category']}</b>\n"
            text += f"   Всего куплено позиций: {shopping['total_bought']}\n\n"
            
            # Аккаунт
            text += f"💎 <b>Статус аккаунта:</b> {account['sub']}\n"
            text += f"   Задач создано: {account['tasks_count']} | Покупок: {account['items_count']}"
            
            # 3. Отправляем сообщение
            await message.answer(text, parse_mode="HTML")
            
    except Exception as e:
        # Логирование ошибки
        print(f"Error in statistic handler: {e}")
        await message.answer("😕 К сожалению, сейчас не удалось загрузить статистику. Попробуйте позже.")

@router.message(F.text == "💎 Подписка")
async def subscription(message: Message, s: AsyncSession):
    if message.from_user is None:
        raise ValueError("Сообщение не от пользователя")
    else:
        user_id = message.from_user.id

        user_sub = await PaymentsRepository.get_user_sub(s, user_id)

        if user_sub is None:
            await message.answer("Вас пока нет в нашей базе данных\n Создайте задачу")
            return

        ans, is_pro = Formater.format_sub_info(user_sub) #type: ignore
        
        if is_pro:
            await message.answer(ans)
            return
        else:
            await message.answer(ans, reply_markup=buy_inline())


@router.message(F.text.regexp(r"^[+-]?\d+\s\d{2}:\d{2}$"))
async def save_settings(message: Message, s: AsyncSession):
    """Сохранить пользовательские настройки"""
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")

    offset_str, time_str = message.text.split() # type: ignore

    await UserRepository.upsert_user_settings(
        s,
        user_id,
        int(offset_str),
        datetime.strptime(time_str, "%H:%M").time()
    )

    await message.answer("Настройки сохранены ✅", reply_markup=new_main_keyboard())


# необходимо чтобы сработал successful_payment
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, s: AsyncSession):

    if message.from_user is None: 
        raise ValueError("у сообщения нет пользователя")
    payment = message.successful_payment
    if payment is None:
        raise ValueError("Не удается получить платеж от телеграмм")
    try:
        tg_payment_id = payment.telegram_payment_charge_id
        provider_payment_id = payment.provider_payment_charge_id
        user_id = message.from_user.id
        amount = payment.total_amount/100 # изначально в копейках


        await PaymentsRepository.save_payment(s, user_id, tg_payment_id, provider_payment_id, amount)
        await PaymentsRepository.change_user_sub(s, user_id, SubscriptionTypes.PREMIUM)

        # выдать подписку
        await message.answer("Оплата прошла успешно!")
    except:
        await message.answer("Приозошла ошибка при обновлении подписки. Пожалуйста напишите в поддержку")
        

# обработка голосового сообщения
@router.message(F.voice, flags={"long_operation": "check_limits"})
async def handle_voice_message(message: Message, bot: Bot, s: AsyncSession):
    # отправляем статус "печать", чтобы пользователь видел активность
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing") #type:ignore
    
    # получаем информацию о файле
    voice = message.voice
    file_info = await bot.get_file(voice.file_id)#type:ignore
    
    # скачиваем файл в объект BytesIO (в оперативную память)
    file_content = await bot.download_file(file_info.file_path)#type:ignore
    
    # отправляем на транскрибацию
    await message.answer("Сообщение в обработке...")
    text = await transcribe_voice(file_content.read(), f"{voice.file_unique_id}.ogg")#type:ignore
    
    # отвечаем пользователю текстом
    if text:
        await process_user_message(message, text, s)
    else:
        await message.reply("К сожалению, не удалось преобразовать голос в текст.")



@router.message(F.reply_to_message)
async def handle_reply(message: Message, s: AsyncSession):
    """
    Обработчик для ответов на сообщения бота, чтобы редактировать задачи и покупки.
    """
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")


    dt_string = await Formater.get_user_time(s, user_id)
    week_info = await Formater.get_week_info(s, user_id)

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

    description = await Formater.make_description(s, id, type, dt_string,request, week_info)
    if description is None: raise ValueError("почему-то не получилось создать описание")

    result = await AiService.ai_edit(description, dt_string, user_id, s)

# ------------------------- 
    # удаляем старую сущность (задачи или покупка)
    await MessageService.delete_entity(s, id, type, user_id)
    # сохраняем новую(ые) сущность(и)
    entities = await MessageService.make_save_new_entity(s, result, user_id)


    if entities is None:

        await message.answer("Какая-то ошибка. попробуйте отредактировать еще раз")
        raise ValueError("Не получилось создать и сохранить сушность")

    if type =="tasks":

        logger.info("попал в отправку задачи")
        for entity in entities:
            logger.info("попал в цикл отправки задач")
            response_text = Formater.format_task(entity, make_task = False) #type: ignore
            await message.answer(
                response_text,
                reply_markup=task_inline(entity.id),  # type: ignore
                parse_mode="Markdown"
            )
    elif type =="shopping_list":
        for entity in entities:
            response_text = Formater.format_shopping_list(entity) #type: ignore
            await message.answer(
                response_text,
                reply_markup=shopping_inline(entity.id), # type: ignore
                parse_mode="Markdown"
            )


    try:
        await message.reply_to_message.delete()
    except:
        print(f"не удалось удалить сообщение c id = {id}")

    

async def process_user_message(message: Message, text:str, s: AsyncSession):
    if message.from_user is not None:
        user_id = message.from_user.id
    else: raise ValueError("сообщение из неизвестного источника")


    dt_string = Formater.get_user_time(s, user_id)
    week_info = Formater.get_week_info(s, user_id)

    if not dt_string:
        await message.answer("Часовой пояс не найден, добавьте его в настройках")
        return

    # проверка на длину (500 слов)
    MAX_TEXT_LENGTH = 6*500
    if len(text) > MAX_TEXT_LENGTH:
        await message.answer("Слишком длинный текст")
        return
    
    promt =f"сегодня {dt_string}, {text}.\n Вот информация о днях недели: {week_info}"
    logger.debug(f"передаю в функцию c LLM время и дату: {dt_string}")
    data_message = await AiService.ai_parse(promt, user_id, s)

    if isinstance(data_message, str):
        await message.answer(f"какая-то ошибка с нейросетью. Текст ошибки {data_message}")
        return

    
    data_list = data_message.get("items")
    if not data_list:
        await message.answer("Не получилось выделить задачу из вашего текста. Пожалуйста напишите подробнее")
        return
    print("до сохранения объекта")
    entitys = await MessageService.make_save_new_entity(s, data_message, user_id)
    if entitys is None:
        raise ValueError("ошибка при сохранении сущности")

    if data_message["type"]=="tasks":
            for entity in entitys:
                response_text = Formater.format_task(entity, make_task = True) #type: ignore

                await message.answer(
                    response_text,
                    reply_markup=task_inline(entity.id), # type: ignore
                    parse_mode="Markdown"
                )

    elif data_message["type"]=="shopping_list":
            for entity in entitys:
                response_text = Formater.format_shopping_list(entity) #type: ignore

                await message.answer(
                    response_text,
                    reply_markup=shopping_inline(entity.id), # type: ignore
                    parse_mode="Markdown"
                )



# --------------------------

@router.message(flags={"long_operation": "check_limits"})
async def new_task(message: Message, s: AsyncSession):
    """Обработчик добавления новой задачи"""
    logger.debug(f"поступило сообщение {message.text}")

    if message.text is None:
        await message.answer("введите текст")
        return
    text = message.text
    await process_user_message(message, text, s)
