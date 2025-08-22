import asyncio
import json
from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import FSInputFile

from exercises.api import generate_task_images
import config

router = Router()


def _load_threads(subject: str) -> dict:
    """Загрузить JSON с thread_id для предмета."""
    file_path = Path(config.THREADS_FILES[subject])
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_threads(subject: str, data: dict) -> None:
    """Сохранить обновлённый JSON с thread_id для предмета."""
    file_path = Path(config.THREADS_FILES[subject])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def _get_or_create_thread(bot: Bot, subject: str, topic_name: str) -> int:
    """Получить thread_id темы или создать новую."""
    threads = _load_threads(subject)
    if topic_name in threads:
        return threads[topic_name]

    chat_id = config.SUBJECT_GROUPS[subject]

    topic = await bot.create_forum_topic(
        chat_id=chat_id,
        name=topic_name
    )

    thread_id = topic.message_thread_id
    threads[topic_name] = thread_id
    _save_threads(subject, threads)

    return thread_id


async def _send_task(bot: Bot, subject: str) -> None:
    """Generate a task image and send it followed by a poll to the right group/thread."""
    result = generate_task_images(
        subject=subject, api_key=config.OPENAI_API_KEY, output_formats=["png"]
    )
    if not result.get("success"):
        return

    # 📌 достаём данные задачи
    meta = result.get("task_meta", {})
    caption = meta
    task_type = result.get("task_type")
    task_data = result.get("task_data", {})
    topic_name = result.get("task_topic")  # имя темы из result

    # 📌 получаем thread_id
    thread_id = await _get_or_create_thread(bot, subject, topic_name)

    # 📌 отправляем картинку
    photo = FSInputFile(result["files"]["png"])
    await bot.send_photo(
        chat_id=config.SUBJECT_GROUPS[subject],
        message_thread_id=thread_id,
        photo=photo,
        caption=caption
    )

    # 📌 формируем poll
    if task_type == "ABCDE":
        options = ["А", "Б", "В", "Г", "Д"]
        letter_map = {"А": 0, "Б": 1, "В": 2, "Г": 3, "Д": 4}
    else:  # COMPARISON и другие
        options = ["А", "Б", "В", "Г"]
        letter_map = {"А": 0, "Б": 1, "В": 2, "Г": 3}

    answer = task_data.get("correct_answer", "").upper()
    if answer not in letter_map:
        raise ValueError(f"Некорректный правильный ответ: {answer}")

    correct = letter_map[answer]

    await bot.send_poll(
        chat_id=config.SUBJECT_GROUPS[subject],
        message_thread_id=thread_id,
        question="Выберите правильный ответ",
        options=options,
        type="quiz",
        correct_option_id=correct,
        is_anonymous=False,
    )


async def _periodic_sender(bot: Bot, interval: int) -> None:
    """Send tasks for all subjects every interval seconds."""
    subjects = config.SUBJECT_GROUPS.keys()
    while True:
        for subject in subjects:
            await _send_task(bot, subject)
        await asyncio.sleep(interval)


@router.startup()
async def _on_start(bot: Bot) -> None:
    """Start the background task on bot startup."""
    interval = getattr(config, "TASK_CREATION_INTERVAL", 60)
    asyncio.create_task(_periodic_sender(bot, interval))
