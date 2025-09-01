import os, uuid
import logging
import aiohttp
from aiogram import Router, F, types, Bot
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path

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

@router.message(F.text.lower() == "tiktok")
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

ALLOWED_EXTS = {"mp4", "mov", "avi", "wmv", "mkv"}
MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100 МБ
TEMP_DIR = Path("temp_videos")

@router.message(TikTokUploadStates.waiting_for_video, F.document)
async def handle_video_document(message: types.Message, state: FSMContext):
    """Обработчик получения видео файла как документа (скачивание через aiohttp)"""
    try:
        # 1) Проверка приватности и авторства
        if message.chat.type != "private" or message.from_user.id != HAN_ID:
            await message.answer("❌ У вас нет прав для использования этой функции.")
            await state.clear()
            return

        document = message.document
        if document is None:
            await message.answer("❌ Не удалось прочитать вложение как документ.")
            return

        # 2) MIME: видео?
        mime = (document.mime_type or "").lower()
        if not mime.startswith("video/"):
            await message.answer(
                "❌ Пожалуйста, отправьте видео файл.\n\n"
                "Поддерживаемые форматы: MP4, AVI, MOV, WMV и другие."
            )
            return

        # 3) Размер (если известен)
        file_size = document.file_size or 0
        if file_size and file_size > MAX_SIZE_BYTES:
            mb = file_size // (1024 * 1024)
            await message.answer(
                f"❌ Размер файла слишком большой ({mb} МБ).\n\n"
                f"Максимальный размер: {MAX_SIZE_BYTES // (1024*1024)} МБ"
            )
            return

        # 4) Подготовка путей
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        original_name = document.file_name or ""
        ext = (original_name.rsplit(".", 1)[-1] if "." in original_name else "").lower()
        if ext not in ALLOWED_EXTS:
            ext = "mp4"  # безопасное дефолтное расширение

        unique = uuid.uuid4().hex[:10]
        file_path: Path = TEMP_DIR / f"video_{message.from_user.id}_{unique}.{ext}"

        # 5) Скачивание через aiohttp
        bot = message.bot
        # 5.1 Получаем file_path у Telegram
        tg_file = await bot.get_file(document.file_id)
        tg_file_path = tg_file.file_path  # типа "documents/file_1234.mp4"

        # 5.2 Формируем URL для скачивания
        # В aiogram v3 токен доступен как bot.token
        download_url = f"https://api.telegram.org/file/bot{bot.token}/{tg_file_path}"

        # 5.3 Качаем потоково
        timeout = aiohttp.ClientTimeout(total=60 * 10)  # до 10 минут на весь файл
        bytes_written = 0
        CHUNK = 1024 * 128  # 128 KiB

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Ошибка скачивания {resp.status}: {text[:200]}")

                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(CHUNK):
                        if not chunk:
                            continue
                        f.write(chunk)
                        bytes_written += len(chunk)
                        # Доп. защита: если известен исходный размер и внезапно переполнили лимит
                        if MAX_SIZE_BYTES and bytes_written > MAX_SIZE_BYTES:
                            raise RuntimeError(
                                "Размер скачиваемого файла превысил допустимый лимит."
                            )

        if bytes_written == 0 or not file_path.exists():
            raise RuntimeError("Файл не был скачан или пуст.")

        # 6) Сохраняем метаданные
        video_data[message.from_user.id] = {
            "file_path": str(file_path),
            "file_name": original_name or file_path.name,
            "file_size": file_size or bytes_written,
            "mime_type": mime,
        }

        # 7) Ответ пользователю и переключение стейта
        size_mb = ((file_size or bytes_written) // (1024 * 1024)) or "неизв."
        await message.answer(
            "✅ Видео получено!\n\n"
            f"📁 Файл: {video_data[message.from_user.id]['file_name']}\n"
            f"📊 Размер: {size_mb} МБ\n\n"
            "📝 Теперь отправьте описание для видео:"
        )
        await state.set_state(TikTokUploadStates.waiting_for_description)

    except Exception as e:
        logger.exception("Ошибка при загрузке видео")
        # Если файл частично успел скачаться — можно попробовать удалить
        try:
            if 'file_path' in locals() and file_path and file_path.exists():
                file_path.unlink(missing_ok=True)
        except Exception:
            pass

        await message.answer(
            "❌ Произошла ошибка при загрузке видео. Попробуйте ещё раз или обратитесь к разработчику."
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