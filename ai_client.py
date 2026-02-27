# ai_client.py
import json
import asyncio

from openai import OpenAI

from config import OPENROUTER_API_KEY


# загружаем переменные из .env в систему, чтобы потом можно было достать


OPENROUTER_API_KEY = OPENROUTER_API_KEY


# Инициализация клиента OpenRouter (OpenAI-совместимый) [web:45][web:49][web:83]
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

async def ask_llm(description: str, system_msg:str) -> dict:
    print("попал в ask_llm")
    user_msg = description

    error = ""
    max_retries=3
    for i in range(max_retries):
        try:
            print("перед получением ответа")
            # Вызов chat completion через OpenRouter [web:45][web:49][web:76]
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-lite-001",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                # JSON-режим: просим модель возвращать JSON-объект [web:81][web:85]
                response_format={"type": "json_object"},
                max_tokens=None,
                temperature=None,
            )
            print("после получения ответа")

            content: str = response.choices[0].message.content
            data = json.loads(content)

            print(data)

            return data  

        except Exception as e:
            print("попал в exception")
            # На проде лучше логировать ошибку
            error=e
            await asyncio.sleep(0.5)

    return error

async def classify_task(description: str) -> dict: 
    print("попал в classify_task")
    system_msg = """
    Ты — ассистент по тайм-менеджменту. Твоя задача — понять сообщение пользователя и определить, содержит ли оно одну или несколько задач.

    ОБЩИЕ ПРАВИЛА:
    1. Ты ВСЕГДА отвечаешь СТРОГО в формате JSON.
    2. Никакого текста вне JSON.
    3. Корневой объект ВСЕГДА содержит поле "type".
    4. Если дата не указано, считай что ее нет

    ВОЗМОЖНЫЕ ТИПЫ ОТВЕТА:

    1) "type": "tasks" — если в тексте есть одна или несколько задач.
    --------------------------------------------------

    ФОРМАТ ОТВЕТА, ЕСЛИ НАЙДЕНЫ ЗАДАЧИ:

    {
    "type": "tasks",
    "items": [
        {
        "category": "тип категории",
        "date": "дата выполнения задачи в формате YYYY-MM-DD или пустая строка",
        "time": "время выполнения в формате HH:MM или пустая строка",
        "remind_date": "дата напоминания в формате YYYY-MM-DD или пустая строка",
        "remind_time": "время напоминания в формате HH:MM или пустая строка",
        "task": "краткое описание задачи"
        }
    ]
    }

    Если в тексте описано несколько задач — добавь каждую отдельным объектом в массив items.

    --------------------------------------------------

    КАТЕГОРИИ ЗАДАЧ (используй ТОЛЬКО их):

    - short_5 — до 5 минут.
    - short_30 — от 5 до 30 минут.
    - short_120 — от 30 минут до 2 часов.
    - long — более 2 часов или сложные проекты.

    Допустимые значения: "short_5", "short_30", "short_120", "long".

    --------------------------------------------------

    ПРИМЕРЫ:

    ПРИМЕР 1:
    ввод:
    сегодня 2026-01-31 10:20, мне нужно завтра купить после обеда наушники для Наташи

    ответ:
    {
    "type": "tasks",
    "items": [
        {
        "category": "short_5",
        "date": "2026-02-01",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "купить наушники Наташе"
        }
    ]
    }

    --------------------------------------------------

    ПРИМЕР 2:
    ввод:
    сегодня 2026-07-19 20:07, нужно через неделю сходить в зал в 19, напомни за день вечером. и нужно сегодня забрать протеин с озона

    ответ:
    {
    "type": "tasks",
    "items": [
        {
        "category": "short_120",
        "date": "2026-07-26",
        "time": "19:00",
        "remind_date": "2026-07-25",
        "remind_time": "18:00",
        "task": "сходить в зал"
        },
        {
        "category": "short_30",
        "date": "2026-07-19",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "забрать протеин с озона"
        }
    ]
    }
    ПРИМЕР 3:
    ввод:
    сегодня 2025-09-10 10:17, напомни мне через 40 минут снять кастрюлю с плиты
    {
    "type": "tasks",
    "items": [
        {
        "category": "short_5",
        "date": "2025-09-10",
        "time": "10:57",
        "remind_date": "2025-09-10",
        "remind_time": "10:57",
        "task": "снять кастрюлю с плиты"
        }
    ]
    }
    --------------------------------------------------


    ВАЖНО:
    - Никогда не возвращай массив или строку на верхнем уровне.
    - Если пользователь не указал даты и других параметров считай что их нет.

    """
    data = await ask_llm(description, system_msg)
    return data
    

async def edit_task(information: dict, date_and_time: str) -> dict:
    """
    получает:
    {
    "request":"изменения от пользователя"
    "category": "тип категории",
    "date": "дата выполнения задачи в формате YYYY-MM-DD или пустая строка",
    "time": "время выполнения в формате HH:MM или пустая строка",
    "remind_date": "дата напоминания в формате YYYY-MM-DD или пустая строка",
    "remind_time": "время напоминания в формате HH:MM или пустая строка",
    "task": "краткое описание задачи"
    }
    """
    system_msg = f'''
    Ты — ассистент по тайм-менеджменту. Твоя задача - получить задачу и коментарий к ней,
    понять коментарий и если нужно изменить задачу и прислать ее в нужном формате.

    
    Пришли новую версию задачи в таком формате:

    {{
    "type": "tasks",
    "items": [
        {{
        "category": "тип категории",
        "date": "дата выполнения задачи в формате YYYY-MM-DD или пустая строка",
        "time": "время выполнения в формате HH:MM или пустая строка",
        "remind_date": "дата напоминания в формате YYYY-MM-DD или пустая строка",
        "remind_time": "время напоминания в формате HH:MM или пустая строка",
        "task": "краткое описание задачи"
        }}
    ]
    }}

    КАТЕГОРИИ ЗАДАЧ (используй ТОЛЬКО их):

    - short_5 — до 5 минут.
    - short_30 — от 5 до 30 минут.
    - short_120 — от 30 минут до 2 часов.
    - long — более 2 часов или сложные проекты.

    Допустимые значения: "short_5", "short_30", "short_120", "long".

    "Перенеси на послезавтра" означает +2 дня к {date_and_time}
    "Перенеси на завтра" означает +1 дня к {date_and_time}
    сейчас время: {date_and_time}

    ОЧЕНЬ ВАЖНО ПРИСЛАТЬ ИМЕННО В ТАКОМ ФОРМАТЕ. УКАЗИВАЙ ПРАВИЛЬНОЕ ВРЕМЯ.
    ЕСЛИ НАЧАЛЬНИК НЕ ГОВОРИТ ЧТО-ТО МЕНЯТЬ, НЕ МЕНЯЙ НИЧЕГО, ДАЖЕ ВРЕМЯ И ДАТУ, ПРОСТО ВСЕ ПЕРЕПИШИ В ДРУГОЙ ФОРМАТ.

    Примеры:
    пример 1 (назначить задачу на сегодня):
    Сегодня Friday, 2026-02-27 22:19. Вот моя задача:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_30",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сходить в пятерочку"
        }}
    ]
    }}
    Вот моя просьба: Сегодня
    Твой ответ:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_30",
        "date": "2026-02-27",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сходить в пятерочку"
        }}
    ]
    }}
    пример 2 (посмотреть задачу):
    Сегодня Friday, 2026-02-27 22:19. Вот моя задача:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_30",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сходить в пятерочку"
        }}
    ]
    }}
    Вот моя просьба: покажи
    Твой ответ:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_30",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сходить в пятерочку"
        }}
    ]
    }}

    пример 3 (изменить задачу):
    Сегодня Friday, 2026-02-27 22:19. Вот моя задача:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_30",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сходить в пятерочку"
        }}
    ]
    }}
    Вот моя просьба: я закажу онлайн напомни через часик

    Твой ответ:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_5",
        "date": "2026-02-27",
        "time": "23:19",
        "remind_date": "2026-02-27",
        "remind_time": "23:19",
        "task": "Заказать еду из пятерочки"
        }}
    ]
    }}

    пример 4 (перенос задачи):
    Сегодня Friday, 2026-02-27 22:19. Вот моя задача:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_120",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сделать матан"
        }}
    ]
    }}
    Вот моя просьба: Перенеси на воскресенье

    Твой ответ:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_120",
        "date": "2026-03-01",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Сделать матан"
        }}
    ]
    }}

    пример 4 (изменить сложность):
    Сегодня Friday, 2026-02-27 22:19. Вот моя задача:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_120",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Выгрузить новую версию бота на сервер"
        }}
    ]
    }}
    Вот моя просьба: это проще

    Твой ответ:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "short_30",
        "date": "",
        "time": "",
        "remind_date": "",
        "remind_time": "",
        "task": "Выгрузить новую версию бота на сервер"
        }}
    ]
    }}

    НЕ МЕНЯЙ ПОЛЯ КОТОРЫЕ ПОЛЬЗОВАТЕЛЬ НЕ ПРОСИТ ИЗМЕНИТЬ!
    '''
    
    description = f'''
    Сегодня {date_and_time}. Вот моя задача:
    {{
    "type": "tasks",
    "items": [
        {{
        "category": "{information["category"]}",
        "date": "{information["date"]}",
        "time": "{information["time"]}",
        "remind_date": "{information["remind_date"]}",
        "remind_time": "{information["remind_time"]}",
        "task": "{information["task"]}"
        }}
    ]
    }}
    Вот моя просьба: {information["request"]}
    '''
    data = await ask_llm(description, system_msg)
    return data