from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📆 Неделя")],
            [KeyboardButton(text="📋 Все задачи"), KeyboardButton(text="⏱ По длительности")],
            [KeyboardButton(text="🛒 Покупки")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


def duration_category_keyboard() -> ReplyKeyboardMarkup:
    """Меню выбора категории по длительности"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="≤ 5 минут"), KeyboardButton(text="≤ 30 минут")],
            [KeyboardButton(text="≤ 2 часов"), KeyboardButton(text="Сложные задачи")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )

def purchase_category_keyboard() -> ReplyKeyboardMarkup:
    """Меню выбора категории по типу покупок"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Продукты"), KeyboardButton(text="Лекарства")],
            [KeyboardButton(text="Для дома"), KeyboardButton(text="Гигиена")],
            [KeyboardButton(text="Техника"), KeyboardButton(text="Одежда")],
            [KeyboardButton(text="Другое"), KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def task_inline(task_id: int) -> InlineKeyboardMarkup:
    """Встроенные кнопки для задачи (выполнено/удалить)"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Выполнено", callback_data=f"task_done:{task_id}")
    kb.button(text="🗑 Удалить", callback_data=f"task_delete:{task_id}")
    kb.adjust(2)
    return kb.as_markup()

def shopping_inline(item_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Купил", callback_data=f"item_bought:{item_id}")
    kb.button(text="🗑 Удалить", callback_data=f"item_delete:{item_id}")
    kb.adjust(2)
    return kb.as_markup()



# Маппинг текста кнопок на внутренние коды категорий
TASK_CATEGORY_MAP = {
    "≤ 5 минут": "short_5",
    "≤ 30 минут": "short_30",
    "≤ 2 часов": "short_120",
    "Сложные задачи": "long",
}

PURCHASE_CATEGORY_MAP = {
    "Продукты":"grocery",
    "Лекарства":"pharmacy",
    "Для дома":"household",
    "Гигиена":"beauty",
    "Техника":"electronics",
    "Одежда":"clothes",
    "Другое":"other",
}
    # - grocery (продукты, напитки)
    # - pharmacy (лекарства)
    # - household (бытовая химия, товары для дома)
    # - beauty (гигиена, косметика)
    # - electronics (техника, батарейки)
    # - clothes (одежда, обувь)
    # - other (все остальное)

# Маппинг для красивого вывода категорий пользователю
READABLE_CATEGORIES = {
    "short_5": "⚡️ До 5 минут",
    "short_30": "⏳ До 30 минут",
    "short_120": "🕒 До 2 часов",
    "long": "🐘 Сложная/долгая"
}
