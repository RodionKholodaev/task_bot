from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📆 Неделя")],
            [KeyboardButton(text="📋 Все задачи")],
            [KeyboardButton(text="⏱ По длительности")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


def category_keyboard() -> ReplyKeyboardMarkup:
    """Меню выбора категории по длительности"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="≤ 5 минут"), KeyboardButton(text="≤ 30 минут")],
            [KeyboardButton(text="≤ 2 часов"), KeyboardButton(text="Сложные задачи")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def task_inline(task_id: int) -> InlineKeyboardMarkup:
    """Встроенные кнопки для задачи (выполнено/удалить)"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Выполнено", callback_data=f"done:{task_id}")
    kb.button(text="🗑 Удалить", callback_data=f"delete:{task_id}")
    kb.adjust(2)
    return kb.as_markup()


# Маппинг текста кнопок на внутренние коды категорий
CATEGORY_MAP = {
    "≤ 5 минут": "short_5",
    "≤ 30 минут": "short_30",
    "≤ 2 часов": "short_120",
    "Сложные задачи": "long",
}

# Маппинг для красивого вывода категорий пользователю
READABLE_CATEGORIES = {
    "short_5": "⚡️ До 5 минут",
    "short_30": "⏳ До 30 минут",
    "short_120": "🕒 До 2 часов",
    "long": "🐘 Сложная/долгая"
}
