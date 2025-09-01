import os
import logging
from aiogram import Router, F, types, Bot
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, TIKTOK_SESSION_ID, HAN_ID
from TikTokUploader.uploader import uploadVideo

router = Router()
bot = Bot(token=BOT_TOKEN)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FSM состояния для загрузки видео в TikTok
class TikTokUploadStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_description = State()
    waiting_for_hashtags = State()
    waiting_for_confirmation = State()

# Временное хранилище данных о видео
video_data = {}

def create_confirmation_keyboard():
    """Создать клавиатуру подтверждения загрузки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Загрузить", callback_data="confirm_upload"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_upload")
    )
    return builder.as_markup()

@router.message(Command("tiktok"))
async def cmd_tiktok(message: types.Message, state: FSMContext):
    """Команда для начала загрузки видео в TikTok (только для HAN в ЛС)"""
    # Проверяем, что это личные сообщения
    if message.chat.type != "private":
        return
    
    # Проверяем, что это HAN
    if message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return
    
    if not TIKTOK_SESSION_ID:
        await message.answer("❌ TikTok Session ID не настроен. Обратитесь к разработчику.")
        return
    
    await message.answer(
        "🎬 Отправьте видео файл в несжатом виде для загрузки в TikTok.\n\n"
        "⚠️ Важно: отправьте видео как файл (не как сжатое видео)."
    )
    await state.set_state(TikTokUploadStates.waiting_for_video)

@router.message(TikTokUploadStates.waiting_for_video, F.document)
async def handle_video_document(message: types.Message, state: FSMContext):
    """Обработчик получения видео файла"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    document = message.document
    
    # Проверяем, что это видео файл
    if not document.mime_type or not document.mime_type.startswith('video/'):
        await message.answer(
            "❌ Пожалуйста, отправьте видео файл.\n\n"
            "Поддерживаемые форматы: MP4, AVI, MOV, WMV и другие."
        )
        return
    
    # Проверяем размер файла (максимум 100 МБ)
    max_size = 100 * 1024 * 1024  # 100 МБ
    if document.file_size > max_size:
        await message.answer(
            f"❌ Размер файла слишком большой ({document.file_size // (1024*1024)} МБ).\n\n"
            f"Максимальный размер: {max_size // (1024*1024)} МБ"
        )
        return
    
    try:
        # Получаем файл
        file = await bot.get_file(document.file_id)
        
        # Создаем папку для временных файлов
        temp_dir = "temp_videos"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Формируем путь к файлу
        file_extension = document.file_name.split('.')[-1] if '.' in document.file_name else 'mp4'
        file_path = os.path.join(temp_dir, f"video_{message.from_user.id}.{file_extension}")
        
        # Скачиваем файл
        await bot.download_file(file.file_path, file_path)
        
        # Сохраняем данные о видео
        video_data[message.from_user.id] = {
            'file_path': file_path,
            'file_name': document.file_name,
            'file_size': document.file_size
        }
        
        await message.answer(
            f"✅ Видео получено!\n\n"
            f"📁 Файл: {document.file_name}\n"
            f"📊 Размер: {document.file_size // (1024*1024)} МБ\n\n"
            f"📝 Теперь отправьте описание для видео:"
        )
        
        await state.set_state(TikTokUploadStates.waiting_for_description)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке видео: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке видео. Попробуйте еще раз или обратитесь к разработчику."
        )
        await state.clear()

@router.message(TikTokUploadStates.waiting_for_video)
async def handle_wrong_video_format(message: types.Message, state: FSMContext):
    """Обработчик неправильного формата видео"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    await message.answer(
        "❌ Пожалуйста, отправьте видео как файл (документ), а не как сжатое видео.\n\n"
        "💡 Чтобы отправить как файл:\n"
        "1. Нажмите на скрепку 📎\n"
        "2. Выберите \"Файл\" или \"Document\"\n"
        "3. Выберите ваше видео"
    )

@router.message(TikTokUploadStates.waiting_for_description, F.text)
async def handle_description(message: types.Message, state: FSMContext):
    """Обработчик получения описания видео"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    if message.from_user.id not in video_data:
        await message.answer("❌ Видео не найдено. Начните заново с команды /tiktok")
        await state.clear()
        return
    
    description = message.text.strip()
    
    if len(description) > 2200:
        await message.answer(
            "❌ Описание слишком длинное. TikTok поддерживает максимум 2200 символов.\n\n"
            f"Текущая длина: {len(description)} символов"
        )
        return
    
    # Сохраняем описание
    video_data[message.from_user.id]['description'] = description
    
    await message.answer(
        f"✅ Описание сохранено!\n\n"
        f"📝 Описание: {description[:100]}{'...' if len(description) > 100 else ''}\n\n"
        f"🏷️ Теперь отправьте хештеги через пробел (например: #tiktok #video #fun):"
    )
    
    await state.set_state(TikTokUploadStates.waiting_for_hashtags)

@router.message(TikTokUploadStates.waiting_for_description)
async def handle_wrong_description_format(message: types.Message, state: FSMContext):
    """Обработчик неправильного формата описания"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    await message.answer("❌ Пожалуйста, отправьте текстовое описание для видео.")

@router.message(TikTokUploadStates.waiting_for_hashtags, F.text)
async def handle_hashtags(message: types.Message, state: FSMContext):
    """Обработчик получения хештегов"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    if message.from_user.id not in video_data:
        await message.answer("❌ Видео не найдено. Начните заново с команды /tiktok")
        await state.clear()
        return
    
    hashtags_text = message.text.strip()
    
    # Парсим хештеги
    hashtags = []
    for word in hashtags_text.split():
        word = word.strip()
        if word:
            # Добавляем # если его нет
            if not word.startswith('#'):
                word = '#' + word
            hashtags.append(word)
    
    if not hashtags:
        await message.answer("❌ Не удалось найти хештеги. Попробуйте еще раз.")
        return
    
    # Сохраняем хештеги
    video_data[message.from_user.id]['hashtags'] = hashtags
    
    # Показываем предпросмотр
    data = video_data[message.from_user.id]
    hashtags_str = ' '.join(hashtags)
    
    preview_text = (
        f"🎬 **Предпросмотр видео для TikTok**\n\n"
        f"📁 **Файл:** {data['file_name']}\n"
        f"📊 **Размер:** {data['file_size'] // (1024*1024)} МБ\n\n"
        f"📝 **Описание:**\n{data['description']}\n\n"
        f"🏷️ **Хештеги:**\n{hashtags_str}\n\n"
        f"Подтвердите загрузку в TikTok:"
    )
    
    await message.answer(
        preview_text,
        reply_markup=create_confirmation_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(TikTokUploadStates.waiting_for_confirmation)

@router.message(TikTokUploadStates.waiting_for_hashtags)
async def handle_wrong_hashtags_format(message: types.Message, state: FSMContext):
    """Обработчик неправильного формата хештегов"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    await message.answer(
        "❌ Пожалуйста, отправьте хештеги в текстовом виде.\n\n"
        "Пример: #tiktok #video #fun\n"
        "или: tiktok video fun"
    )

@router.callback_query(F.data == "confirm_upload", TikTokUploadStates.waiting_for_confirmation)
async def handle_confirm_upload(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик подтверждения загрузки"""
    # Проверяем, что это личные сообщения от HAN
    if callback.message.chat.type != "private" or callback.from_user.id != HAN_ID:
        await callback.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    if callback.from_user.id not in video_data:
        await callback.answer("❌ Видео не найдено. Начните заново с команды /tiktok")
        await state.clear()
        return
    
    await callback.answer()
    await callback.message.edit_text("⏳ Загружаем видео в TikTok...")
    
    try:
        data = video_data[callback.from_user.id]
        
        # Формируем полный текст для TikTok (описание + хештеги)
        title_with_hashtags = data['description'] + ' ' + ' '.join(data['hashtags'])
        
        logger.info(f"Начинаем загрузку видео в TikTok: {data['file_name']}")
        
        # Загружаем видео в TikTok
        result = uploadVideo(
            session_id=TIKTOK_SESSION_ID,
            video=data['file_path'],
            title=title_with_hashtags,
            tags=data['hashtags'],
            users=[],
            url_prefix="us",
            schedule_time=0
        )
        
        if result:
            await callback.message.edit_text(
                f"✅ **Видео успешно загружено в TikTok!**\n\n"
                f"📁 Файл: {data['file_name']}\n"
                f"📝 Описание: {data['description'][:50]}...\n"
                f"🏷️ Хештеги: {' '.join(data['hashtags'])[:50]}...",
                parse_mode="Markdown"
            )
            logger.info(f"Видео успешно загружено в TikTok: {data['file_name']}")
        else:
            await callback.message.edit_text(
                "❌ **Ошибка при загрузке видео в TikTok**\n\n"
                "Возможные причины:\n"
                "• Неверный Session ID\n"
                "• Проблемы с интернет-соединением\n"
                "• Ограничения TikTok\n\n"
                "Попробуйте еще раз позже или обратитесь к разработчику.",
                parse_mode="Markdown"
            )
            logger.error(f"Ошибка при загрузке видео в TikTok: {data['file_name']}")
        
    except Exception as e:
        logger.error(f"Исключение при загрузке видео в TikTok: {e}")
        await callback.message.edit_text(
            f"❌ **Произошла ошибка при загрузке видео**\n\n"
            f"Ошибка: {str(e)[:100]}...\n\n"
            f"Обратитесь к разработчику.",
            parse_mode="Markdown"
        )
    
    finally:
        # Очищаем временные данные и файл
        if callback.from_user.id in video_data:
            data = video_data[callback.from_user.id]
            if os.path.exists(data['file_path']):
                try:
                    os.remove(data['file_path'])
                    logger.info(f"Временный файл удален: {data['file_path']}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении временного файла: {e}")
            
            del video_data[callback.from_user.id]
        
        await state.clear()

@router.callback_query(F.data == "cancel_upload", TikTokUploadStates.waiting_for_confirmation)
async def handle_cancel_upload(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик отмены загрузки"""
    # Проверяем, что это личные сообщения от HAN
    if callback.message.chat.type != "private" or callback.from_user.id != HAN_ID:
        await callback.answer("❌ У вас нет прав для использования этой функции.")
        await state.clear()
        return
    
    await callback.answer()
    await callback.message.edit_text("❌ Загрузка видео в TikTok отменена.")
    
    # Очищаем временные данные и файл
    if callback.from_user.id in video_data:
        data = video_data[callback.from_user.id]
        if os.path.exists(data['file_path']):
            try:
                os.remove(data['file_path'])
                logger.info(f"Временный файл удален: {data['file_path']}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
        
        del video_data[callback.from_user.id]
    
    await state.clear()

# Команда для проверки статуса TikTok функции
@router.message(Command("tiktok_status"))
async def cmd_tiktok_status(message: types.Message):
    """Проверка статуса TikTok функции"""
    # Проверяем, что это личные сообщения от HAN
    if message.chat.type != "private" or message.from_user.id != HAN_ID:
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return
    
    status_text = "🔍 **Статус TikTok функции:**\n\n"
    
    if TIKTOK_SESSION_ID:
        status_text += "✅ TikTok Session ID: настроен\n"
    else:
        status_text += "❌ TikTok Session ID: не настроен\n"
    
    # Проверяем папку для временных файлов
    temp_dir = "temp_videos"
    if os.path.exists(temp_dir):
        temp_files = [f for f in os.listdir(temp_dir) if f.startswith('video_')]
        status_text += f"📁 Временные файлы: {len(temp_files)}\n"
    else:
        status_text += "📁 Папка временных файлов: не создана\n"
    
    status_text += f"\n💾 Активных сессий загрузки: {len(video_data)}\n"
    
    status_text += "\n📚 **Команды:**\n"
    status_text += "• `/tiktok` - загрузить видео\n"
    status_text += "• `/tiktok_status` - проверить статус\n"
    
    await message.answer(status_text, parse_mode="Markdown")