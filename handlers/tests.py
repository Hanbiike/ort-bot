from aiogram import Router, F, types
from aiogram.types import WebAppInfo
from config import QUIZ_WEBAPP_BASE_URL

router = Router()

TEST_BUTTONS = ["тесты", "тесттер"]

@router.message(F.text.lower().in_(TEST_BUTTONS))
async def list_tests(message: types.Message):
    kb = [[types.KeyboardButton(text=f"Тест №{i}") for i in range(1,6)],
          [types.KeyboardButton(text=f"Тест №{i}") for i in range(6,11)],
          [types.KeyboardButton(text="Главное меню")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выберите тест:", reply_markup=keyboard)

@router.message(F.text.regexp(r"^Тест №(\d+)$"))
async def start_test(message: types.Message, regexp: types.Match[str]):
    num = int(regexp.group(1))
    if not 1 <= num <= 10:
        return
    webapp_url = f"{QUIZ_WEBAPP_BASE_URL}?test={num}"
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Запустить", web_app=WebAppInfo(url=webapp_url))],
                  [types.KeyboardButton(text="Главное меню")]],
        resize_keyboard=True,
    )
    await message.answer(f"Тест №{num}", reply_markup=kb)
