from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice
from db.task_repository import TaskRepository 
from db.shopping_repository import ShoppingRepository 
from config import YOOKASSA_TOKEN
from db.database import get_session

# роутер для подключения к файлу бота
router = Router()

# обработка нажатия на кнопку выполнено
@router.callback_query(F.data.startswith("task_done:"))
async def done_task(callback: CallbackQuery):
    async with get_session() as s:
        task_id = int(callback.data.split(":")[1]) # type: ignore
        if await TaskRepository.mark_done(s, task_id, callback.from_user.id):
            await callback.message.edit_text("✅ Выполнено") # type: ignore
        await callback.answer()

# обработка кнопки удалить задачу
@router.callback_query(F.data.startswith("task_delete:"))
async def delete_task(callback: CallbackQuery):
    async with get_session() as s:
        task_id = int(callback.data.split(":")[1]) # type: ignore
        if await TaskRepository.delete_task(s, task_id, callback.from_user.id):
            await callback.message.delete() # type: ignore
        await callback.answer()

# обработка нажатия на кнопку предмет куплен
@router.callback_query(F.data.startswith("item_bought:"))
async def bought(callback: CallbackQuery):
    async with get_session() as s:
        item_id = int(callback.data.split(":")[1]) # type: ignore
        if await ShoppingRepository.delete_item(s, item_id, callback.from_user.id):
            await callback.message.edit_text("✅ Куплен") # type: ignore
        await callback.answer()

# обработка кнопки удалить предмет
@router.callback_query(F.data.startswith("item_delete:"))
async def delete_item(callback: CallbackQuery):
    async with get_session() as s:
        item_id = int(callback.data.split(":")[1]) # type: ignore
        if await ShoppingRepository.delete_item(s, item_id, callback.from_user.id):
            await callback.message.delete() # type: ignore
        await callback.answer()



@router.callback_query(F.data == "buy_pro_subscription")
async def process_buy_callback(callback: CallbackQuery):
    prices = [LabeledPrice(label="Подписка", amount=99*100)]

    if callback.message is None:
        raise ValueError("Что-то не то при попытке купить подписку")

    # Отправляем инвойс
    await callback.message.answer_invoice(
        title="Подписка",
        description="Подписка на бота",
        payload="subscription",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=prices
    )
    
    # Обязательно отвечаем на колбэк, чтобы убрать "часики" на кнопке
    await callback.answer()