# ai_client.py
import os
import json
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI

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

# даем короткое название для сложной конструкции
TaskCategory = Literal["short_5", "short_30", "short_120", "long"]


async def classify_task(description: str) -> TaskCategory: # возвращаем один из вариантов из TaskCategory
    """
    Отправляет описание задачи в GPT-3.5 Turbo через OpenRouter
    и возвращает одну из категорий:
    - short_5   (до 5 минут)
    - short_30  (до 30 минут)
    - short_120 (до 2 часов)
    - long      (долгие/сложные)
    В случае ошибки возвращает 'short_30' как дефолт.
    """
    # Промпт с требованием вернуть ЧИСТЫЙ JSON [web:81][web:85]
    system_msg = (
        "Ты помощник, который классифицирует задачи по длительности.\n"
        "Всегда отвечай ТОЛЬКО JSON-объектом без пояснений, в одной строке.\n"
        "Формат ответа: {\"category\": \"short_5\"}.\n"
        "Допустимые значения category: \"short_5\", \"short_30\", \"short_120\", \"long\".\n"
        "- short_5: очень простые задачи, которые можно сделать за несколько минут.\n"
        "- short_30: задачи примерно до 30 минут.\n"
        "- short_120: задачи от 30 минут до 2 часов.\n"
        "- long: сложные или долгие задачи больше 2 часов.\n"
    )

    user_msg = f"Определи категорию для задачи: \"{description}\""

    try:
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

        content: str = response.choices[0].message.content
        data = json.loads(content)

        category: Optional[str] = data.get("category")
        if category not in ("short_5", "short_30", "short_120", "long"):
            # Фоллбек, если модель вернула что-то странное
            return "short_30"  # дефолтная категория

        return category  # type: ignore[return-value]

    except Exception as e:
        # На проде лучше логировать ошибку
        print(f"Error calling OpenRouter: {e}")
        return "short_30"
