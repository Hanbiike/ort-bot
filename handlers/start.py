from aiogram import Router, F, Bot, types
from aiogram.filters.command import Command
from aiogram.filters import CommandStart
from aiogram.types import Chat
from aiogram.utils.keyboard import InlineKeyboardBuilder

from methods.users import update_user_lang, user_lang
from methods.admins import is_admin
from keyboards import menu
from config import HAN_ID, CHANNEL_ID, BOT_TOKEN

# Константы
# ...existing code...

router = Router()
bot = Bot(token=BOT_TOKEN)

def create_language_keyboard():
    """Создать клавиатуру для выбора языка."""
    kb = [
        [
            types.KeyboardButton(text="Русский язык"),
            types.KeyboardButton(text="Кыргыз тили")
        ],
    ]
    return types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите язык / тил таңданыз"
    )

def create_social_media_keyboard():
    """Создать клавиатуру для подписки на соцсети."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Instagram", url="https://www.instagram.com/han.ort245/"))
    builder.row(types.InlineKeyboardButton(text="TikTok", url="https://www.tiktok.com/@askat.ort245"))
    builder.row(types.InlineKeyboardButton(text="YouTube", url="https://www.youtube.com/@han.ort245"))
    builder.row(types.InlineKeyboardButton(text="Telegram", url="https://t.me/+LpE1_DQetocxNjZi"))
    builder.row(types.InlineKeyboardButton(text="Проверить подписку", callback_data="check_podpiska"))
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    if message.chat.type != "private":
        await message.answer("💬 Напишите мне в личные сообщения, чтобы начать подготовку к ОРТ: @han_ort_bot", reply_markup=types.ReplyKeyboardRemove())
        return
    
    keyboard = create_language_keyboard()
    await message.answer(
        "Привет! Я помогу вам подготовиться к ОРТ. Выберите язык, на котором будете сдавать ОРТ\n\n"
        "Салам! Мен сизге ЖРТга даярданууга жардам берем. ЖРТны тапшыра турган тилди тандаңыз?",
        reply_markup=keyboard
    )

@router.message(F.text.casefold() == "русский язык")
async def lang_ru(message: types.Message):
    """Обработчик выбора русского языка."""
    if message.chat.type != "private":
        await message.answer("💬 Напишите мне в личные сообщения, чтобы начать подготовку к ОРТ: @han_ort_bot", reply_markup=types.ReplyKeyboardRemove())
        return
    
    user_id = message.from_user.id
    await update_user_lang(user_id, "ru")
    await message.reply("Хороший выбор!", reply_markup=types.ReplyKeyboardRemove())
    keyboard = create_social_media_keyboard()
    await message.answer("Для того чтобы я работал подпишитесь на наши соцсети!", reply_markup=keyboard)

@router.message(F.text.casefold() == "кыргыз тили")
async def lang_kg(message: types.Message):
    """Обработчик выбора кыргызского языка."""
    if message.chat.type != "private":
        await message.answer("💬 ЖРТга даярданууну баштоо үчүн жеке билдирүү жазыңыз: @han_ort_bot", reply_markup=types.ReplyKeyboardRemove())
        return
    
    user_id = message.from_user.id
    await update_user_lang(user_id, "kg")
    await message.reply("Жакшы тандоо!", reply_markup=types.ReplyKeyboardRemove())
    keyboard = create_social_media_keyboard()
    await message.answer("Мен иштешим үчүн соцтармактарыбызга катталыңыз!", reply_markup=keyboard)

@router.callback_query(F.data == "check_podpiska")
async def check_subscription(callback: types.CallbackQuery):
    """Проверить подписку пользователя."""
    if callback.message.chat.type != "private":
        await callback.answer("💬 Напишите мне в личные сообщения, чтобы начать подготовку к ОРТ: @han_ort_bot", show_alert=True, reply_markup=types.ReplyKeyboardRemove())
        return
    
    try:
        user_id = callback.from_user.id
        user_channel_status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        lang = await user_lang(user_id)
        
        if is_admin(user_id):
            await callback.answer(text="Спасибо за подписку!", show_alert=True)
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
            await menu.menu_admin(callback.message)
            return
        
        if user_channel_status.status != 'left':
            text = "Спасибо за подписку!" if lang == "ru" else "Жазылганыз үчүн рахмат!"
            await callback.answer(text=text, show_alert=True)
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
            if lang == "ru":
                await menu.menu_ru(callback.message)
            elif lang == "kg":
                await menu.menu_kg(callback.message)
                
    except Exception as e:
        print(f"An error occurred: {e}")
