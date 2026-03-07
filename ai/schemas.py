from datetime import date, time
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class TaskLLMResponse(BaseModel):
    task: str
    category: Literal["short_5", "short_30", "short_120", "long"]
    deadline_date: date | None = Field(default=None, alias="date")
    deadline_time: time | None = Field(default=None, alias="time")

    remind_date: date | None = Field(default=None)
    remind_time: time | None = Field(default=None)

    # разрешаю использовать alias для получения данных
    class Config:
        populate_by_name = True
    # преобразуем пустую строку в None
    @field_validator(
        "deadline_date",
        "deadline_time",
        "remind_date",
        "remind_time",
        mode="before"
    )
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

class ItemLLMResponse(BaseModel):
    category: Literal["grocery", "pharmacy", "household", "beauty", "electronics", "clothes", "other"]
    item: str
    amount: float | None = Field(default=None)
    unit: Literal["кг", "л", "шт", "м"] | None = Field(default=None)

"""
получаю либо это
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
либо это
    {
    "type": "shopping_list",
    "items": [
        {
        "category": "строго из списка ниже",
        "item": "название товара",
        "amount": "число (float) или пустая строка",
        "unit": "строго из списка ниже или пустая строка"
        }
    ]
    }
"""