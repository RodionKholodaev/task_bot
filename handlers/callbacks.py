from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import mark_done, delete_task

# роутер для подключения к файлу бота
router = Router()

# обработка нажатия на кнопку выполнено
@router.callback_query(F.data.startswith("done:"))
async def done(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    if mark_done(task_id, callback.from_user.id):
        await callback.message.edit_text("✅ Выполнено")
    await callback.answer()

# обработка кнопки удалить
@router.callback_query(F.data.startswith("delete:"))
async def delete(callback: CallbackQuery):
    """Обработчик нажатия на кнопку 'Удалить'"""
    task_id = int(callback.data.split(":")[1])
    if delete_task(task_id, callback.from_user.id):
        await callback.message.delete()
    await callback.answer()
