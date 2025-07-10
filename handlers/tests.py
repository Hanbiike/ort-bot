from aiogram import Router, F, types
from aiogram.types import WebAppInfo, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import QUIZ_WEBAPP_BASE_URL

router = Router()

TEST_BUTTONS = ["тесты", "тесттер"]


@router.message(F.text.lower().in_(TEST_BUTTONS))
async def choose_topic(message: types.Message):
    """Prompt user to choose a test topic."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Арифметика", callback_data="topic_arithmetic"))
    builder.row(InlineKeyboardButton(text="Проценты", callback_data="topic_percent"))
    await message.answer("Выберите тему:", reply_markup=builder.as_markup())


@router.callback_query(F.data == "topic_arithmetic")
async def list_arithmetic_tests(callback: types.CallbackQuery):
    """Show available arithmetic tests."""
    builder = InlineKeyboardBuilder()
    for i in range(1, 17):
        builder.button(
            text=str(i),
            web_app=WebAppInfo(url=f"{QUIZ_WEBAPP_BASE_URL}?topic=arithmetics&test={i}")
        )
    builder.adjust(1)
    await callback.message.answer("Выберите тест:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "topic_percent")
async def list_percent_tests(callback: types.CallbackQuery):
    """Show available percent tests."""
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(
            text=str(i),
            web_app=WebAppInfo(url=f"{QUIZ_WEBAPP_BASE_URL}?topic=percents&test={i}")
        )
    builder.adjust(1)
    await callback.message.answer("Выберите тест:", reply_markup=builder.as_markup())
    await callback.answer()
