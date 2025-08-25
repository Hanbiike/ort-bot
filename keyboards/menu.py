from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from methods.users import *
from methods.admins import is_admin

router = Router()

SUBJECT_LINKS = [
    ("Математика & Физика", "https://t.me/han_ort_math"),
    ("Русская грамматика", "https://t.me/han_ort_rus"),
    ("Кыргыз грамматикасы", "https://t.me/han_ort_kg"),
    ("English", "https://t.me/han_ort_eng"),
    ("Химия", "https://t.me/han_ort_himbio"),
    ("Биология", "https://t.me/+wSH95Svv4N9hZWZi"),
    ("CLOUD - RU", "https://t.me/han_ort_cloud"),
    ("CLOUD - KG", "https://t.me/han_jrt_cloud"),
]

UNIVERSITIES = [
    ("АУЦА", "https://t.me/studauca"),
    ("АЛА-ТОО", "https://t.me/studalatoo"),
    ("БГУ", "https://t.me/studbgu"),
    ("КНУ & КГЮА", "https://t.me/studknu"),
    ("КРСУ", "https://t.me/studkrsu"),
    ("МАНАС", "https://t.me/+GcmvEBnMX4MxMDVi"),
    ("МУК", "https://t.me/studmuk"),
    ("ОШГУ", "https://t.me/+d8FZlWdjmRRlZjZi"),
    ("Политех КГТУ", "https://t.me/studkstu"),
    ("Медицинские вузы", "https://t.me/studmedkg"),
]


def build_inline_subjects():
    builder = InlineKeyboardBuilder()
    for text, url in SUBJECT_LINKS:
        builder.row(types.InlineKeyboardButton(text=text, url=url))
    return builder.as_markup()


def build_universities_keyboard():
    builder = InlineKeyboardBuilder()
    for text, url in UNIVERSITIES:
        builder.row(types.InlineKeyboardButton(text=text, url=url))
    return builder.as_markup()


def build_reply_keyboard(lang="ru", admin=False):
    if lang == "kg":
        kb = [
            [types.KeyboardButton(text="Чек-лист"), types.KeyboardButton(text="Материалдар")],
            [types.KeyboardButton(text="Тесттер")],
            [types.KeyboardButton(text="Университеттер")],
            [types.KeyboardButton(text="Жардам"), types.KeyboardButton(text="Тил / язык")],
            [types.KeyboardButton(text="ЖРТ баллдарын эсептөө"), types.KeyboardButton(text="Профиль")],
        ]
        if admin:
            kb.append([types.KeyboardButton(text="Рассылка")])
            kb.append([types.KeyboardButton(text="Статистика")])
        placeholder = "Эмнеден баштайлы?"
    else:
        kb = [
            [types.KeyboardButton(text="Чек-лист"), types.KeyboardButton(text="Материалы")],
            [types.KeyboardButton(text="Тесты")],
            [types.KeyboardButton(text="Университеты")],
            [types.KeyboardButton(text="Помощь"), types.KeyboardButton(text="Язык / тил")],
            [types.KeyboardButton(text="Подсчет баллов ОРТ"), types.KeyboardButton(text="Профиль")],
        ]
        if admin:
            kb[-1].append(types.KeyboardButton(text="Рассылка"))
            kb.append([types.KeyboardButton(text="Статистика")])
        placeholder = "С чего начнем?"
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder=placeholder)
    return keyboard


async def menu_ru(message: types.Message):
    if is_admin(message.from_user.id):
        await menu_admin(message)
        return
    if message.chat.type != "private":
        await message.answer("💬 Напишите мне в личные сообщения, чтобы начать подготовку к ОРТ: @han_ort_bot")
        return
    await message.answer(
        "Теперь же когда вы выполнили все условия, получите в награду бесплатные материалы, которые вы искали!",
        reply_markup=build_inline_subjects(),
    )
    keyboard = build_reply_keyboard(lang="ru", admin=False)
    await message.answer("Что ж, начнем подготовку!", reply_markup=keyboard)


async def menu_kg(message: types.Message):
    if is_admin(message.from_user.id):
        await menu_admin(message)
        return
    if message.chat.type != "private":
        await message.answer("💬 ЖРТга даярданууну баштоо үчүн жеке билдирүү жазыңыз: @han_ort_bot")
        return
    await message.answer(
        "Эми сиз бардык шарттарды аткаргандан кийин, сиз издеген бекер материалдар менен сыйланасыз!",
        reply_markup=build_inline_subjects(),
    )
    keyboard = build_reply_keyboard(lang="kg", admin=False)
    await message.answer("Эмесе даярдоону баштайлы!", reply_markup=keyboard)


async def menu_admin(message: types.Message):
    await message.answer(
        "Теперь же когда вы выполнили все условия, получите в награду бесплатные материалы, которые вы искали!",
        reply_markup=build_inline_subjects(),
    )
    keyboard = build_reply_keyboard(lang="ru", admin=True)
    await message.answer("Что ж, начнем подготовку!", reply_markup=keyboard)


@router.message(F.text.lower() == "материалы")
async def materials_ru(message: types.Message):
    await message.answer("Бесплатные материалы, которые вы искали!", reply_markup=build_inline_subjects())


@router.message(F.text.lower() == "материалдар")
async def materials_kg(message: types.Message):
    await message.answer("Сиз издеген бекер материалдар!", reply_markup=build_inline_subjects())


@router.message(F.text.lower() == "университеты")
async def universities_ru(message: types.Message):
    await message.reply("Университеты:", reply_markup=build_universities_keyboard())


@router.message(F.text.lower() == "университеттер")
async def universities_kg(message: types.Message):
    await message.reply("Университеттер:", reply_markup=build_universities_keyboard())


@router.message(F.text.lower() == "чек-лист")
async def checklist(message: Message):
    user_id = message.from_user.id
    lang = await user_lang(user_id)
    if lang == "ru":
        await message.reply_document(
            "BQACAgIAAxkBAAIdKGaZQf7AVafCmQdH-nBHWSSVUAwzAAK0PQACtniJS-TGlnduvl9fNQQ",
            caption="Чек-лист - перечень тем, которые будут на ОРТ. Лишних и отсутствующих тем нет, то есть не нужно изучать то, что не указано в чек-листе",
        )
        await message.answer_document(
            "BQACAgIAAxkBAAIdKmaZQf4uP36Sw3IPeiizu-3FNkXIAAJbNwACF4QQSEYWy3Sk4hxjNQQ",
            caption="Все формулы по математике основного теста",
        )
    else:
        await message.reply_document(
            "BQACAgIAAxkBAALZr2dciF6699u_aO3yXm-FHn6ZHKJtAAL9PQACtniJS8a7xkayUwcMNgQ",
            caption="Чек-лист - ЖРТда боло турган темалардын тизмеси. Керексиз же жетишпеген темалар жок, башкача айтканда, чек-листте көрсөтүлбөгөн нерселерди изилдөөнүн кереги жок",
        )
        await message.answer_document(
            "BQACAgIAAxkBAAIdKmaZQf4uP36Sw3IPeiizu-3FNkXIAAJbNwACF4QQSEYWy3Sk4hxjNQQ",
            caption="Негизги тесттин баардык формулалары",
        )


@router.message(F.text.lower() == "помощь")
@router.message(F.text.lower() == "жардам")
async def help_handler(message: types.Message):
    user_id = message.from_user.id
    lang = await user_lang(user_id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Telegram", url="https://t.me/R_anony"))
    builder.row(types.InlineKeyboardButton(text="WhatsApp", url="https://wa.me/996700044504"))
    if lang == "kg":
        await message.answer(
            "Курска жазылгыныз келсе же кенеш керек болсо админге жазыныз. (Эгер сизге үй тапшырмасы же башка тапшырма боюнча жардам керек болсо, анда ар бир тапшырма үчүн жардамдын баасы 100 сомдон 1000 сомго чейин)",
            reply_markup=builder.as_markup(),
        )
    else:
        await message.answer(
            "Если вы хотите записаться на курс или же нужна консультация, то напишите админу. (Если нужна помощь с домашней работой или любой другой задачей, то помощь стоит от 100 до 1000 сом за каждое задание)",
            reply_markup=builder.as_markup(),
        )


@router.message(F.text.lower() == "язык / тил")
@router.message(F.text.lower() == "тил / язык")
async def cmd_lang(message: types.Message):
    kb = [[types.KeyboardButton(text="Русский"), types.KeyboardButton(text="Кыргызча")]]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, input_field_placeholder="Выберите язык / тил таңданыз"
    )
    await message.answer(
        "Выберите язык, на котором будете сдавать ОРТ\n\nЖРТны тапшыра турган тилди тандаңыз?", reply_markup=keyboard
    )


@router.message(F.text.lower() == "кыргызча")
async def set_lang_kg(message: types.Message):
    user_id = message.from_user.id
    await update_user_lang(user_id, "kg")
    await menu_kg(message)


@router.message(F.text.lower() == "русский")
async def set_lang_ru(message: types.Message):
    user_id = message.from_user.id
    await update_user_lang(user_id, "ru")
    await menu_ru(message)


@router.message(F.text.lower() == "главное меню")
async def main_menu_ru(message: types.Message):
    await menu_ru(message)


@router.message(F.text.lower() == "башкы меню")
async def main_menu_kg(message: types.Message):
    await menu_kg(message)
