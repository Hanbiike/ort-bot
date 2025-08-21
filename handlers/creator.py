"""Periodic task sender.

Generates mathematical tasks and posts them to the group chat. After the
image is sent, a poll with answer options is posted immediately. The poll
options use only the letters "А", "Б", "В", "Г" and optionally "Д" depending
on the task type.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot, Router
from aiogram.types import FSInputFile

from exercises.api import generate_task_images
import config


router = Router()


async def _send_task(bot: Bot) -> None:
    """Generate a task image and send it followed by a poll."""
    result = generate_task_images(
        api_key=config.OPENAI_API_KEY, output_formats=["png"]
    )
    if not result.get("success"):
        return

    meta = result.get("task_meta", {})
    caption = (
        f"Класс: {meta.get('класс')}\n"
        f"Тема: {meta.get('тема')}\n"
        f"Подтема: {meta.get('подтема')}\n"
        f"Сложность: {meta.get('сложность')}"
    )

    photo = FSInputFile(result["files"]["png"])
    await bot.send_photo(config.GROUP_ID, photo, caption=caption)

    task_type = result.get("task_type")
    task_data = result.get("task_data", {})

    if task_type == "ABCDE":
        options = ["А", "Б", "В", "Г", "Д"]
        letter_map = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
        correct = letter_map.get(task_data.get("correct_answer", "").upper(), 0)
    else:  # COMPARISON and others with four options
        options = ["А", "Б", "В", "Г"]
        symbols = [">", "<", "=", "недостаточно данных"]
        ans = task_data.get("correct_answer")
        correct = symbols.index(ans) if ans in symbols else 0

    await bot.send_poll(
        config.GROUP_ID,
        "Выберите правильный ответ",
        options=options,
        type="quiz",
        correct_option_id=correct,
        is_anonymous=False,
    )


async def _periodic_sender(bot: Bot, interval: int) -> None:
    """Send tasks to the group every ``interval`` seconds."""
    while True:
        await _send_task(bot)
        await asyncio.sleep(interval)


@router.startup()
async def _on_start(bot: Bot) -> None:
    """Start the background task on bot startup."""
    interval = getattr(config, "TASK_CREATION_INTERVAL", 3600)
    asyncio.create_task(_periodic_sender(bot, interval))

