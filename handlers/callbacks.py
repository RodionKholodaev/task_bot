from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.database import mark_done, delete_task, mark_bought, delete_item

# роутер для подключения к файлу бота
router = Router()

# обработка нажатия на кнопку выполнено
@router.callback_query(F.data.startswith("task_done:"))
async def done(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    if mark_done(task_id, callback.from_user.id):
        await callback.message.edit_text("✅ Выполнено")
    await callback.answer()

# обработка кнопки удалить задачу
@router.callback_query(F.data.startswith("task_delete:"))
async def delete(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])
    if delete_task(task_id, callback.from_user.id):
        await callback.message.delete()
    await callback.answer()

# обработка нажатия на кнопку предмет куплен
@router.callback_query(F.data.startswith("item_bought:"))
async def done(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])
    if mark_bought(item_id, callback.from_user.id):
        await callback.message.edit_text("✅ Куплен")
    await callback.answer()

# обработка кнопки удалить предмет
@router.callback_query(F.data.startswith("item_delete:"))
async def delete(callback: CallbackQuery):

    item_id = int(callback.data.split(":")[1])
    if delete_item(item_id, callback.from_user.id):
        await callback.message.delete()
    await callback.answer()
