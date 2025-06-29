from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, WebAppInfo
from methods.profiles import ProfileManager
from methods.scan import DocScanner
from methods.users import user_lang
from methods.validators import validate_score
from keyboards import menu
from config import OWNER_ID, MAX_SCORE, SCANNER_WEBAPP_URL
import json
import base64
from io import BytesIO

router = Router()
profile_manager = ProfileManager()

class ProfileStates(StatesGroup):
    waiting_for_sheet = State()
    waiting_for_name = State()
    waiting_for_score = State()

MESSAGES = {
    "profile_not_found": {
        "ru": "❌ Профиль не найден.\nХотите создать новый профиль?",
        "kg": "❌ Профиль табылган жок.\nЖаңы профиль түзгүңүз келеби?"
    },
    "profile_template": {
        "ru": "📋 Ваш профиль:\n\n👤 ФИО: {name}\n📊 Балл ОРТ: {score}\n🏆 Место в рейтинге: {rank}/{total}",
        "kg": "📋 Сиздин профилиңиз:\n\n👤 ФАА: {name}\n📊 ЖРТ баллы: {score}\n🏆 Рейтингдеги орун: {rank}/{total}"
    },
    "update_profile": {
        "ru": "Обновить профиль",
        "kg": "Профилди жаңыртуу"
    },
    "rating": {
        "ru": "Рейтинг",
        "kg": "Рейтинг"
    },
    "yes": {
        "ru": "✅ Да",
        "kg": "✅ Ооба"
    },
    "no": {
        "ru": "❌ Нет",
        "kg": "❌ Жок"
    },
    "menu": {
        "ru": "Главное меню",
        "kg": "Башкы меню"
    },
    "enter_full_name": {
        "ru": "Введите ваше ФИО:",
        "kg": "ФААңызды жазыңыз:"
    },
    "enter_score": {
        "ru": "Введите ваш балл ОРТ (от 0 до 245):",
        "kg": "ЖРТ баллыңызды жазыңыз (0дон 245ге чейин):"
    },
    "invalid_score": {
        "ru": "❌ Неверный формат балла. Введите число от 0 до 245.",
        "kg": "❌ Туура эмес балл. 0дон 245ге чейинки санды жазыңыз."
    },
    "profile_submitted": {
        "ru": "✅ Ваш профиль отправлен на проверку.",
        "kg": "✅ Сиздин профилиңиз текшерүүгө жөнөтүлдү."
    },
    "send_photo": {
        "ru": "📸 Отправить фото",
        "kg": "📸 Сүрөт жөнөтүү"
    },
    "send_result_sheet": {
        "ru": "📄 Отправьте фото листа с результатами по одному. Когда закончите, напишите 'Готово'.",
        "kg": "📄 Натыйжалар барагынын сүрөтүн бирден жөнөтүңүз. Бүтсөңүз 'Бүттү' деп жазыңыз."
    },
    "sheet_received": {
        "ru": "✅ Фото получено. Отправьте следующее или напишите 'Готово'.",
        "kg": "✅ Сүрөт алынды. Кийинкисин жөнөтүңүз же 'Бүттү' деп жазыңыз."
    },
    "photo_received": {
        "ru": "✅ Фото отправлено на проверку.",
        "kg": "✅ Сүрөт текшерүүгө жөнөтүлдү."
    },
    "profile_creation_rejected": {
        "ru": "❌ Создание профиля отменено.",
        "kg": "❌ Профиль түзүү жокко чыгарылды."
    },
    "error_occurred": {
        "ru": "❌ Произошла ошибка. Попробуйте позже.",
        "kg": "❌ Ката кетти. Кийинчерээк кайталаңыз."
    },
    "approve": {
        "ru": "✅ Подтвердить",
        "kg": "✅ Тастыктоо"
    },
    "reject": {
        "ru": "❌ Отклонить",
        "kg": "❌ Четке кагуу"
    },
    "new_profile_admin": {
        "ru": "📝 Новый профиль от {user}:\n👤 ФИО: {name}\n📊 Балл ОРТ: {score}",
        "kg": "📝 Жаңы профиль {user}:\n👤 ФАА: {name}\n📊 ЖРТ баллы: {score}"
    },
    "rankings_header": {
        "ru": "🏆 Рейтинг по баллам ОРТ:",
        "kg": "🏆 ЖРТ баллдары боюнча рейтинг:"
    },
    "ranking_line": {
        "ru": "{pos}. {name} - {score} баллов\n",
        "kg": "{pos}. {name} - {score} балл\n"
    },
    "user_ranking_line": {
        "ru": "\n... Ваше место: {rank}. {name} - {score} баллов\n",
        "kg": "\n... Сиздин орунуңуз: {rank}. {name} - {score} балл\n"
    },
    "total_participants": {
        "ru": "\n\nВсего участников: {total}",
        "kg": "\n\nБардык катышуучулар: {total}"
    }
}

def get_message(key: str, lang: str) -> str:
    return MESSAGES.get(key, {}).get(lang, "Message not found")

async def get_profile_keyboard(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[
            types.KeyboardButton(text=get_message("update_profile", lang)),
            types.KeyboardButton(text=get_message("rating", lang)),
            types.KeyboardButton(text=get_message("menu", lang))
        ]],
        resize_keyboard=True
    )

async def get_confirmation_keyboard(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[
            types.KeyboardButton(text=get_message("yes", lang)),
            types.KeyboardButton(text=get_message("no", lang)),
            types.KeyboardButton(text=get_message("menu", lang))
        ]],
        resize_keyboard=True
    )

async def get_scan_keyboard(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[
            types.KeyboardButton(
                text=get_message("send_photo", lang),
                web_app=WebAppInfo(url=SCANNER_WEBAPP_URL)
            )
        ], [
            types.KeyboardButton(text=get_message("menu", lang))
        ]],
        resize_keyboard=True
    )

@router.message(F.text.lower().in_(["профиль", "profile"]))
@router.message(Command("profile"))
async def show_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await user_lang(user_id)
    profile = await profile_manager.get_profile(user_id)
    
    if not profile:
        await message.answer(
            get_message("profile_not_found", lang),
            reply_markup=await get_confirmation_keyboard(lang)
        )
        return

    rank, total = await profile_manager.get_user_rank(user_id)
    text = await profile_manager.format_profile(profile, rank, total, lang)
    
    await message.answer(
        text,
        reply_markup=await get_profile_keyboard(lang)
    )

@router.message(F.text.in_(["✅ Да", "✅ Ооба"]))
async def confirm_profile_creation(message: types.Message, state: FSMContext):
    await update_profile_start(message, state)

@router.message(F.text.in_(["❌ Нет", "❌ Жок"]))
async def reject_profile_creation(message: types.Message):
    lang = await user_lang(message.from_user.id)
    text = get_message("profile_creation_rejected", lang)
    
    await message.answer(text)

@router.message(F.text.lower().in_(["обновить профиль", "профилди жаңыртуу"]))
async def update_profile_start(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)
    await message.answer(
        get_message("send_result_sheet", lang)
    )
    await state.set_state(ProfileStates.waiting_for_sheet)

DONE_WORDS = ["готово", "бүттү"]

@router.message(ProfileStates.waiting_for_sheet, F.photo)
@router.message(ProfileStates.waiting_for_sheet, F.document)
async def process_result_sheet(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)
    try:
        file_id = None
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        if not file_id:
            return
        file = await message.bot.get_file(file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        scanner = DocScanner()
        processed = scanner.scan_bytes(image_bytes)
        bio = BytesIO(processed)
        bio.name = "scan.jpg"
        caption = (
            f"📄 Скан от <a href='tg://user?id={message.from_user.id}'>"
            f"{message.from_user.full_name}</a>"
        )
        await message.bot.send_photo(
            OWNER_ID, bio, caption=caption, parse_mode="HTML"
        )
        await message.answer(get_message("sheet_received", lang))
    except Exception as e:
        print(f"Error processing sheet: {e}")
        await message.answer(get_message("error_occurred", lang))


@router.message(ProfileStates.waiting_for_sheet, F.text.casefold().in_(DONE_WORDS))
async def finish_sheet_upload(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)
    await message.answer(get_message("enter_full_name", lang))
    await state.set_state(ProfileStates.waiting_for_name)

@router.message(ProfileStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    lang = await user_lang(message.from_user.id)
    
    await message.answer(
        get_message("enter_score", lang)
    )
    await state.set_state(ProfileStates.waiting_for_score)

@router.message(ProfileStates.waiting_for_score)
async def process_score(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)
    
    try:
        score = validate_score(message.text)
        user_data = await state.get_data()
        
        if not user_data.get('full_name'):
            await message.answer(get_message("error_occurred", lang))
            await state.clear()
            return
            
        await profile_manager.add_pending_profile(
            message.from_user.id,
            user_data['full_name'],
            score
        )
        
        await message.answer(
            get_message("profile_submitted", lang),
            reply_markup=await get_profile_keyboard(lang)
        )
        
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=get_message("approve", lang),
                callback_data=f"approve_{message.from_user.id}"
            ),
            InlineKeyboardButton(
                text=get_message("reject", lang),
                callback_data=f"reject_{message.from_user.id}"
            )
        ]])
        
        username = message.from_user.username or message.from_user.full_name
        await message.bot.send_message(
            OWNER_ID,
            get_message("new_profile_admin", lang).format(
                user=f"@{username}",
                name=user_data['full_name'],
                score=score
            ),
            parse_mode="HTML",
            reply_markup=markup
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(get_message("invalid_score", lang))
    except Exception as e:
        print(f"Error in process_score: {e}")
        await message.answer(get_message("error_occurred", lang))
        await state.clear()

@router.callback_query(F.data.startswith("approve_"))
async def approve_profile_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Недостаточно прав")
        return
    
    try:
        user_id = int(callback.data.split("_")[1])
        if await profile_manager.approve_profile(user_id):
            await callback.message.edit_text(
                f"✅ Профиль пользователя {user_id} подтвержден",
                reply_markup=None
            )
            await callback.bot.send_message(
                user_id,
                "✅ Ваш профиль был подтвержден администратором!"
            )
        else:
            await callback.answer("Профиль не найден в ожидающих проверку")
    except Exception as e:
        await callback.answer("Произошла ошибка при обработке запроса")
    finally:
        await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_profile_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Недостаточно прав")
        return
    
    try:
        user_id = int(callback.data.split("_")[1])
        if await profile_manager.reject_profile(user_id):
            await callback.message.edit_text(
                f"❌ Профиль пользователя {user_id} отклонен",
                reply_markup=None
            )
            await callback.bot.send_message(
                user_id,
                "❌ Ваш профиль был отклонен администратором. "
                "Пожалуйста, создайте новый профиль с корректными данными."
            )
        else:
            await callback.answer("Профиль не найден в ожидающих проверку")
    except Exception as e:
        await callback.answer("Произошла ошибка при обработке запроса")
    finally:
        await callback.answer()

@router.message(F.text == "Pending Profiles")
async def list_pending_profiles(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
        
    pending = await profile_manager.get_pending_profiles()
    if not pending:
        await message.answer("Нет профилей ожидающих проверку")
        return
        
    text = "📝 Профили на проверку:\n\n"
    for profile in pending:
        text += (f"👤 ID: {profile['user_id']}\n"
                f"📋 ФИО: {profile['full_name']}\n"
                f"📊 Балл ОРТ: {profile['орт_score']}\n"
                f"⏰ Создан: {profile['timestamp']}\n\n")
    
    await message.answer(text)

@router.message(F.text.lower() == "рейтинг")
async def show_rankings(message: types.Message):
    user_id = message.from_user.id
    lang = await user_lang(user_id)
    
    rankings_text = await profile_manager.format_rankings(
        user_id,
        lang,
        top_count=10
    )

    await message.answer(rankings_text)


@router.message(F.web_app_data)
async def handle_scan(message: types.Message):
    """Receive photo from WebApp and forward to admin."""
    lang = await user_lang(message.from_user.id)
    try:
        data = json.loads(message.web_app_data.data)
        image_data = data.get("image")
        if image_data:
            header, b64 = image_data.split(",", 1)
            image_bytes = base64.b64decode(b64)
            scanner = DocScanner()
            processed = scanner.scan_bytes(image_bytes)
            bio = BytesIO(processed)
            bio.name = "scan.jpg"
            caption = (
                f"📄 Скан от <a href='tg://user?id={message.from_user.id}'>"
                f"{message.from_user.full_name}</a>"
            )
            await message.bot.send_photo(
                OWNER_ID, bio, caption=caption, parse_mode="HTML"
            )
            await message.answer(
                get_message("photo_received", lang),
                reply_markup=await get_profile_keyboard(lang)
            )
        else:
            await message.answer(get_message("error_occurred", lang))
    except Exception as e:
        print(f"Error processing webapp data: {e}")
        await message.answer(get_message("error_occurred", lang))
