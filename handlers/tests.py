from aiogram import Router, F, types
from aiogram.types import WebAppInfo, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import QUIZ_WEBAPP_BASE_URL
import json
from pathlib import Path

# Path to the tests description file
TESTS_DATA_PATH = Path(__file__).resolve().parents[1] / "docs" / "tests.json"
IMG_DIR = TESTS_DATA_PATH.parent / "img"

# Load tests information
with open(TESTS_DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

# Separate thematic topics and CEATM tests
THEMES: dict[str, str] = data.get("themes", {})
CEATM: dict[str, str] = data.get("ceatm", {})

router = Router()

TEST_BUTTONS = ["тесты", "тесттер"]


@router.message(F.text.lower().in_(TEST_BUTTONS))
async def tests_menu(message: types.Message):
    """Show initial tests menu with type selection."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="ТЕМАТИЧЕСКИЕ", callback_data="tests_thematic")
    )
    builder.row(
        InlineKeyboardButton(text="ЦООМО", callback_data="tests_ceatm")
    )
    await message.answer("Выберите раздел тестов:", reply_markup=builder.as_markup())


@router.callback_query(F.data == "tests_thematic")
async def choose_topic(callback: types.CallbackQuery):
    """Prompt user to choose a thematic test topic."""
    builder = InlineKeyboardBuilder()
    for key, title in THEMES.items():
        builder.row(InlineKeyboardButton(text=title, callback_data=f"topic_{key}"))
    await callback.message.answer("Выберите тему:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "tests_ceatm")
async def choose_ceatm(callback: types.CallbackQuery):
    """Show available CEATM tests."""
    builder = InlineKeyboardBuilder()
    for key, title in CEATM.items():
        builder.row(InlineKeyboardButton(text=title, callback_data=f"ceatm_{key}"))
    await callback.message.answer("Выберите тест ЦООМО:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("topic_"))
async def list_thematic_tests(callback: types.CallbackQuery):
    """Show available tests for the chosen thematic topic."""
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


@router.callback_query(F.data.startswith("ceatm_"))
async def ceatm_parts(callback: types.CallbackQuery):
    """Show part selection for a CEATM test."""
    ceatm_key = callback.data.split("_", 1)[1]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="ЧАСТЬ 1",
            web_app=WebAppInfo(url=f"{QUIZ_WEBAPP_BASE_URL}?topic={ceatm_key}&test=1")
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ЧАСТЬ 2",
            web_app=WebAppInfo(url=f"{QUIZ_WEBAPP_BASE_URL}?topic={ceatm_key}&test=2")
        )
    )
    await callback.message.answer("Выберите часть:", reply_markup=builder.as_markup())
    await callback.answer()
