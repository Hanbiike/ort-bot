from aiogram import Router, types, F
from methods.users import user_lang

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
