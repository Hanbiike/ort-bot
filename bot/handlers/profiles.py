from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from ..methods.profiles import ProfileManager
from ..methods.users import user_lang
from ..methods.validators import validate_score
from ..keyboards import menu
from ..config import OWNER_ID, MAX_SCORE

router = Router()
profile_manager = ProfileManager()
get_message = profile_manager.get_message

class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_score = State()

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
        get_message("enter_full_name", lang)
    )
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
        
        await message.answer(get_message("profile_submitted", lang))
        
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

