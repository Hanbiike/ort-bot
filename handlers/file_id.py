from aiogram import Router, types, F
from methods.users import user_lang
from config import OWNER_ID
from aiogram import Bot
router = Router()

FILE_TYPES = [
    "photo",
    "document",
    "video",
    "audio",
    "voice",
    "animation",
    "video_note",
    "sticker",
]

@router.message(F.content_type.in_(FILE_TYPES))
async def send_file_id(message: types.Message):
    if message.chat.type != "private":
        return

    content_type = message.content_type
    file_id = None

    if content_type == "photo":
        file_id = message.photo[-1].file_id
    elif content_type == "document":
        file_id = message.document.file_id
    elif content_type == "video":
        file_id = message.video.file_id
    elif content_type == "audio":
        file_id = message.audio.file_id
    elif content_type == "voice":
        file_id = message.voice.file_id
    elif content_type == "animation":
        file_id = message.animation.file_id
    elif content_type == "video_note":
        file_id = message.video_note.file_id
    elif content_type == "sticker":
        file_id = message.sticker.file_id

    if file_id:
        lang = await user_lang(message.from_user.id)
        text = "ID файла:\n```\n{}\n```" if lang == "ru" else "Файлдын IDси:\n```\n{}\n```"
        await message.answer(text.format(file_id), parse_mode="Markdown")

@router.message(F.text.lower() == "group_id")
async def send_group_id(message: types.Message, bot: Bot):
    # Только владелец может запросить
    if message.from_user.id != OWNER_ID:
        return

    group_id = message.chat.id
    lang = await user_lang(message.from_user.id)  # твоя функция выбора языка

    if lang == "ru":
        text = f"ID группы:\n<code>{group_id}</code>"
    else:
        text = f"Группанын IDси:\n<code>{group_id}</code>"

    # Отправляем в ЛС админу
    await bot.send_message(chat_id=OWNER_ID, text=text, parse_mode="HTML")

    # (опционально) уведомляем в чате, что id ушёл в личку
    await message.reply("✅ ID группы отправлен админу в личку")