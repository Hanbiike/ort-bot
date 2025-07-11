from aiogram import Router, F, types
from aiogram.types import WebAppInfo, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import QUIZ_WEBAPP_BASE_URL
import json
from pathlib import Path

THEMES_PATH = Path(__file__).resolve().parents[1] / "docs" / "themes.json"
IMG_DIR = THEMES_PATH.parent / "img"

with open(THEMES_PATH, encoding="utf-8") as f:
    TOPICS: dict[str, str] = json.load(f)

router = Router()

TEST_BUTTONS = ["тесты", "тесттер"]


@router.message(F.text.lower().in_(TEST_BUTTONS))
async def choose_topic(message: types.Message):
    """Prompt user to choose a test topic."""
    builder = InlineKeyboardBuilder()
    for key, title in TOPICS.items():
        builder.row(InlineKeyboardButton(text=title, callback_data=f"topic_{key}"))
    await message.answer("Выберите тему:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("topic_"))
async def list_tests(callback: types.CallbackQuery):
    """Show available tests for the chosen topic."""
    topic = callback.data.split("_", 1)[1]
    builder = InlineKeyboardBuilder()
    topic_dir = IMG_DIR / topic
    test_numbers = sorted(
        int(p.stem.split("_")[1]) for p in topic_dir.glob("test_*.json")
    )
    for i in test_numbers:
        builder.button(
            text=str(i),
            web_app=WebAppInfo(url=f"{QUIZ_WEBAPP_BASE_URL}?topic={topic}&test={i}")
        )
    builder.adjust(1)
    await callback.message.answer("Выберите тест:", reply_markup=builder.as_markup())
    await callback.answer()
