from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.task_repository import TaskRepository 
from db.shopping_repository import ShoppingRepository 
# роутер для подключения к файлу бота
router = Router()

# обработка нажатия на кнопку выполнено
@router.callback_query(F.data.startswith("task_done:"))
async def done_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1]) # type: ignore
    if TaskRepository.mark_done(task_id, callback.from_user.id):
        await callback.message.edit_text("✅ Выполнено") # type: ignore
    await callback.answer()

# обработка кнопки удалить задачу
@router.callback_query(F.data.startswith("task_delete:"))
async def delete_task(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1]) # type: ignore
    if TaskRepository.delete_task(task_id, callback.from_user.id):
        await callback.message.delete() # type: ignore
    await callback.answer()

# обработка нажатия на кнопку предмет куплен
@router.callback_query(F.data.startswith("item_bought:"))
async def bought(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1]) # type: ignore
    if ShoppingRepository.delete_item(item_id, callback.from_user.id):
        await callback.message.edit_text("✅ Куплен") # type: ignore
    await callback.answer()

# обработка кнопки удалить предмет
@router.callback_query(F.data.startswith("item_delete:"))
async def delete_item(callback: CallbackQuery):

    item_id = int(callback.data.split(":")[1]) # type: ignore
    if ShoppingRepository.delete_item(item_id, callback.from_user.id):
        await callback.message.delete() # type: ignore
    await callback.answer()
