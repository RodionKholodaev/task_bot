# ai_client.py
import os
import json
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI

from datetime import datetime, timezone, timedelta

# загружаем переменные из .env в систему, чтобы потом можно было достать
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set in environment")

# Инициализация клиента OpenRouter (OpenAI-совместимый) [web:45][web:49][web:83]
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)



# UTC+time_delta
time_delta = 3
offset = timezone(timedelta(hours=time_delta))
now = datetime.now(offset)
date = now.date()
time = now.time()

async def classify_task(description: str) -> dict: 
    print("попал в classify_task")
    system_msg = """Ты — ассистент по тайм-менеджменту. Твоя задача — классифицировать задачу пользователя по времени выполнения и разделять ее на составные части.
    
    ПРАВИЛА ОТВЕТА:
    1. Отвечай СТРОГО в формате JSON.
    2. Никакого лишнего текста, только объект.
    3. Формат: {"category": "тип категории",
        "date":"дата когда нужно выполнить задачу",
        "time": "время в которое нужно будет выполнить задачу",
        "task": "краткое описание задачи"
        }

    КАТЕГОРИИ:
    - short_5: до 5 минут (очень быстро).
    - short_30: от 5 до 30 минут.
    - short_120: от 30 минут до 2 часов.
    - long: более 2 часов или сложные проекты.

    Допустимые значения: "short_5", "short_30", "short_120", "long".

    ПРИМЕР 1:
    сегодня 2026-01-31, мне нужно завтра купить после обеда наушники для Наташи.
    Твой ответ: 
    {"category": "short_5",
        "date":"2026-02-01",
        "time": "",
        "task": "купить наушники Наташе"
    }
    ПРИМЕР 2:
    сегодня 2025-08-20, сходить в МФЦ в понедельник в 17:00.
    Твой ответ:
    {"category": "short_120",
        "date":"2025-08-25",
        "time": "17:00",
        "task": "сходить в МФЦ"
    }
    """

    user_msg = description

    try:
        print("перед получением ответа")
        # Вызов chat completion через OpenRouter [web:45][web:49][web:76]
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            # JSON-режим: просим модель возвращать JSON-объект [web:81][web:85]
            response_format={"type": "json_object"},
            max_tokens=50,
            temperature=0.1,
        )
        print("после получения ответа")

        content: str = response.choices[0].message.content
        data = json.loads(content)

        return data  

    except Exception as e:
        print("попал в exception")
        # На проде лучше логировать ошибку
        print(f"Error calling OpenRouter: {e}")
        return "short_30"
