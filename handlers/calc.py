from aiogram import Router, types, F
import re
import math
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class OrTScoreStates(StatesGroup):
    waiting_for_method_choice = State()
    waiting_for_percentage_scores = State()
    waiting_for_correct_answers = State()

@router.message(F.text.casefold() == "подсчет баллов орт")
async def ort_score_calculator(message: types.Message):
    """Handler for calculating ORT scores."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="По процентам", callback_data="method_percentage"),
        InlineKeyboardButton(text="По количеству правильных ответов", callback_data="method_correct_answers"),
        width=1
    )
    await message.answer(
        text="Выберите способ подсчета баллов:",
        reply_markup=builder.as_markup()
    )

@router.message(F.text.casefold() == "жрт баллдарын эсептөө")
async def ort_score_calculator_kg(message: types.Message):
    """Handler for calculating ORT scores in Kyrgyz."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пайыз менен", callback_data="method_percentage_kg"),
        InlineKeyboardButton(text="Туура жооптордун саны менен", callback_data="method_correct_answers_kg"),
        width=1
    )
    await message.answer(
        text="Баллдарды эсептөө ыкмасын тандаңыз:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("method_"))
async def method_choice_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    choice = callback.data
    await callback.message.delete_reply_markup()
    
    if choice == "method_percentage":
        text = ("Введите проценты правильно отвеченных по разделам в формате:\n"
                "Математика, Чтение, Грамматика (максимум 100% каждый)")
    elif choice == "method_percentage_kg":
        text = ("Бөлүмдөр боюнча туура жооптордун пайызын киргизиңиз:\n"
                "Математика, Окуу, Грамматика (ар бири максимум 100%)")
    elif choice == "method_correct_answers_kg":
        text = ("Бөлүмдөр боюнча туура жооптордун санын киргизиңиз:\n"
                "Математика, Окуу, Грамматика")
    else:
        text = ("Введите количество правильных ответов по разделам в формате:\n"
                "Математика, Чтение, Грамматика")

    state_data = {"lang": "kg" if choice.endswith("_kg") else "ru"}
    await state.set_data(state_data)
    await state.set_state(OrTScoreStates.waiting_for_percentage_scores if "percentage" in choice 
                         else OrTScoreStates.waiting_for_correct_answers)
    await callback.message.answer(text)

def calculate_percentage_scores(scores):
    """Helper function to calculate scores from percentages."""
    math_score = int(scores[0] * 0.65 + 0.5)
    reading_score = int(scores[1] * 1.2 + 0.5)
    grammar_score = int(scores[2] * 0.6 + 0.5)
    total_score = math_score + reading_score + grammar_score
    return math_score, reading_score, grammar_score, total_score

def calculate_correct_answers(scores):
    """Helper function to calculate scores from correct answers."""
    math_score = int(scores[0] * (65 / 60) + 0.5)
    reading_score = scores[1] * 2
    grammar_score = scores[2] * 2
    total_score = math_score + reading_score + grammar_score
    return math_score, reading_score, grammar_score, total_score

@router.message(OrTScoreStates.waiting_for_percentage_scores)
async def calculate_score_percentage(message: types.Message, state: FSMContext):
    try:
        state_data = await state.get_data()
        lang = state_data.get("lang", "ru")
        scores = [float(x.strip(' %,')) for x in re.split(r'[,\s]+', message.text) if x.strip()]
        
        if len(scores) != 3:
            await message.answer("Үч санды киргизиңиз (боштук же үтүр менен)" if lang == "kg" 
                               else "Пожалуйста, введите три числа (можно через пробел или запятую)")
            return

        if any(not 0 <= score <= 100 for score in scores):
            await message.answer("Пайыздар 0дон 100гө чейин болушу керек. Кайра аракет кылыңыз" if lang == "kg"
                               else "Проценты должны быть от 0 до 100. Попробуйте снова")
            return

        math_score, reading_score, grammar_score, total_score = calculate_percentage_scores(scores)
        
        if lang == "kg":
            await message.answer(
                f"Сиздин жалпы ЖРТ баллыңыз: {total_score}\n"
                f"Математика: {math_score}\n"
                f"Окуу: {reading_score}\n"
                f"Грамматика: {grammar_score}"
            )
        else:
            await message.answer(
                f"Ваш общий балл ОРТ по процентам: {total_score}\n"
                f"Математика: {math_score}\n"
                f"Чтение: {reading_score}\n"
                f"Грамматика: {grammar_score}"
            )
        await state.clear()
    except (ValueError, IndexError):
        await message.answer("Үч санды боштук же үтүр менен киргизиңиз" if lang == "kg"
                           else "Пожалуйста, введите три числа через пробел или запятую")

@router.message(OrTScoreStates.waiting_for_correct_answers)
async def calculate_score_correct_answers(message: types.Message, state: FSMContext):
    try:
        state_data = await state.get_data()
        lang = state_data.get("lang", "ru")
        scores = [int(x.strip()) for x in re.split(r'[,\s]+', message.text) if x.strip()]
        
        if len(scores) != 3:
            await message.answer("Үч санды киргизиңиз (боштук же үтүр менен)" if lang == "kg"
                               else "Пожалуйста, введите три числа (можно через пробел или запятую)")
            return

        max_scores = [60, 60, 30]
        if any(not 0 <= score <= max_score for score, max_score in zip(scores, max_scores)):
            await message.answer("Жооптордун максималдуу саны ашып кетти: мат≤60, окуу≤60, грам≤30. Кайра аракет кылыңыз" if lang == "kg"
                               else "Превышен максимум ответов: мат≤60, чтение≤60, грам≤30. Попробуйте снова")
            return

        math_score, reading_score, grammar_score, total_score = calculate_correct_answers(scores)
        
        if lang == "kg":
            await message.answer(
                f"Сиздин жалпы ЖРТ баллыңыз: {total_score}\n"
                f"Математика: {math_score}\n"
                f"Окуу: {reading_score}\n"
                f"Грамматика: {grammar_score}"
            )
        else:
            await message.answer(
                f"Ваш общий балл ОРТ: {total_score}\n"
                f"Математика: {math_score}\n"
                f"Чтение: {reading_score}\n"
                f"Грамматика: {grammar_score}"
            )
        await state.clear()
    except (ValueError, IndexError):
        await message.answer("Үч санды боштук же үтүр менен киргизиңиз" if lang == "kg"
                           else "Пожалуйста, введите три числа через пробел или запятую")

@router.inline_query()
async def inline_ort_calc(query: types.InlineQuery):
    text = query.query.strip()
    
    if not text:
        return await query.answer(
            results=[
                types.InlineQueryResultArticle(
                    id="1",
                    title="Подсчет баллов ОРТ / ЖРТ упайларын эсептөө",
                    description="Введите три числа / Үч санды киргизиңиз",
                    input_message_content=types.InputTextMessageContent(
                        message_text="Введите три числа через пробел / Үч санды боштук менен киргизиңиз\n"
                                   "Например / Мисалы: 80 90 85"
                    )
                )
            ],
            cache_time=1
        )

    try:
        numbers = [float(x.strip()) for x in text.split() if x.strip()]
        if len(numbers) != 3:
            raise ValueError

        # Percentage calculation
        perc_numbers = [min(100, n) for n in numbers]
        math_score_perc, reading_score_perc, grammar_score_perc, total_score_perc = calculate_percentage_scores(perc_numbers)

        # Correct answers calculation
        ans_numbers = [min(60, numbers[0]), min(60, numbers[1]), min(30, numbers[2])]
        math_score_ans, reading_score_ans, grammar_score_ans, total_score_ans = calculate_correct_answers(ans_numbers)

        percentage_result = (
            f"📊 Результаты ОРТ (по процентам):\n"
            f"Общий балл: {total_score_perc}\n"
            f"Математика: {math_score_perc}\n"
            f"Чтение: {reading_score_perc}\n"
            f"Грамматика: {grammar_score_perc}\n\n"
            f"📊 ЖРТ жыйынтыктары (пайыздар боюнча):\n"
            f"Жалпы балл: {total_score_perc}\n"
            f"Математика: {math_score_perc}\n"
            f"Окуу: {reading_score_perc}\n"
            f"Грамматика: {grammar_score_perc}"
        )

        answers_result = (
            f"✅ Результаты ОРТ (по ответам):\n"
            f"Общий балл: {total_score_ans}\n"
            f"Математика: {math_score_ans}\n"
            f"Чтение: {reading_score_ans}\n"
            f"Грамматика: {grammar_score_ans}\n\n"
            f"✅ ЖРТ жыйынтыктары (жооптор боюнча):\n"
            f"Жалпы балл: {total_score_ans}\n"
            f"Математика: {math_score_ans}\n"
            f"Окуу: {reading_score_ans}\n"
            f"Грамматика: {grammar_score_ans}"
        )

        await query.answer(
            results=[
                types.InlineQueryResultArticle(
                    id="1",
                    title="📊 По процентам / Пайыздар менен",
                    description=f"Общий балл / Жалпы балл: {total_score_perc}",
                    input_message_content=types.InputTextMessageContent(
                        message_text=percentage_result
                    )
                ),
                types.InlineQueryResultArticle(
                    id="2",
                    title="✅ По ответам / Жооптор менен",
                    description=f"Общий балл / Жалпы балл: {total_score_ans}",
                    input_message_content=types.InputTextMessageContent(
                        message_text=answers_result
                    )
                )
            ],
            cache_time=1
        )
    except (ValueError, IndexError):
        await query.answer(
            results=[
                types.InlineQueryResultArticle(
                    id="1",
                    title="Ошибка / Ката",
                    description="Введите три числа через пробел\nҮч санды боштук менен киргизиңиз",
                    input_message_content=types.InputTextMessageContent(
                        message_text="Подсчет баллов ОРТ / ЖРТ упайларын эсептөө\n"
                                   "Например / Мисалы: @han_ort_bot 80 90 85"
                    )
                )
            ],
            cache_time=1
        )
