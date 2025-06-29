from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from ..methods.users import user_lang, update_user_lang
from ..methods.admins import is_admin

router = Router()

async def menu_ru(message: types.Message):
    # Check if user is admin
    if is_admin(message.from_user.id):
        await menu_admin(message)
        return
    
    if message.chat.type != "private":
        await message.answer("💬 Напишите мне в личные сообщения, чтобы начать подготовку к ОРТ: @han_ort_bot")
        return
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Математика & Физика",
        url="https://t.me/han_ort_math")
    )
    builder.row(types.InlineKeyboardButton(
        text="Русская грамматика", url="https://t.me/han_ort_rus")
    )
    builder.row(types.InlineKeyboardButton(
        text="Кыргыз грамматикасы", url="https://t.me/han_ort_kg")
    )
    builder.row(types.InlineKeyboardButton(
        text="English",
        url="https://t.me/han_ort_eng")
    )
    builder.row(types.InlineKeyboardButton(
        text="Химия & Биология", url="https://t.me/han_ort_himbio")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - RU", url="https://t.me/han_ort_cloud")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - KG", url="https://t.me/han_jrt_cloud")
    )
    await message.answer("Теперь же когда вы выполнили все условия, получите в награду бесплатные материалы, которые вы искали!", reply_markup=builder.as_markup())
    kb = [
        [
            types.KeyboardButton(text="Чек-лист"),
            types.KeyboardButton(text="Материалы")
        ],
        [
            types.KeyboardButton(text="Университеты"),
        ],
        [
            types.KeyboardButton(text="Помощь"),
            types.KeyboardButton(text="Язык / тил")
        ],
        [
            types.KeyboardButton(text="Подсчет баллов ОРТ"),
            types.KeyboardButton(text="Профиль")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="С чего начнем?"
    )
    await message.answer("Что ж, начнем подготовку!", reply_markup=keyboard)


async def menu_kg(message: types.Message):
    # Check if user is admin
    if is_admin(message.from_user.id):
        await menu_admin(message)
        return
    
    if message.chat.type != "private":
        await message.answer("💬 ЖРТга даярданууну баштоо үчүн жеке билдирүү жазыңыз: @han_ort_bot")
        return
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Математика & Физика",
        url="https://t.me/han_ort_math")
    )
    builder.row(types.InlineKeyboardButton(
        text="Русская грамматика", url="https://t.me/han_ort_rus")
    )
    builder.row(types.InlineKeyboardButton(
        text="Кыргыз грамматкасы", url="https://t.me/han_ort_kg")
    )
    builder.row(types.InlineKeyboardButton(
        text="English",
        url="https://t.me/han_ort_eng")
    )
    builder.row(types.InlineKeyboardButton(
        text="Химия & Биология", url="https://t.me/han_ort_himbio")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - RU", url="https://t.me/han_ort_cloud")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - KG", url="https://t.me/han_jrt_cloud")
    )
    await message.answer("Эми сиз бардык шарттарды аткаргандан кийин, сиз издеген бекер материалдар менен сыйланасыз!", reply_markup=builder.as_markup())
    kb = [
        [
            types.KeyboardButton(text="Чек-лист"),
            types.KeyboardButton(text="Материалдар")
        ],
        [
            types.KeyboardButton(text="Университеттер"),
        ],
        [
            types.KeyboardButton(text="Жардам"),
            types.KeyboardButton(text="Тил / язык"),
        ],
        [
            types.KeyboardButton(text="ЖРТ баллдарын эсептөө"),
            types.KeyboardButton(text="Профиль")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Эмнеден баштайлы?"
    )
    await message.answer("Эмесе даярдоону баштайлы!", reply_markup=keyboard)

async def menu_admin(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Математика & Физика",
        url="https://t.me/han_ort_math")
    )
    builder.row(types.InlineKeyboardButton(
        text="Русская грамматика", url="https://t.me/han_ort_rus")
    )
    builder.row(types.InlineKeyboardButton(
        text="Кыргыз грамматкасы", url="https://t.me/han_ort_kg")
    )
    builder.row(types.InlineKeyboardButton(
        text="English",
        url="https://t.me/han_ort_eng")
    )
    builder.row(types.InlineKeyboardButton(
        text="Химия & Биология", url="https://t.me/han_ort_himbio")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - RU", url="https://t.me/han_ort_cloud")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - KG", url="https://t.me/han_jrt_cloud")
    )
    await message.answer("Теперь же когда вы выполнили все условия, получите в награду бесплатные материалы, которые вы искали!", reply_markup=builder.as_markup())
    kb = [
        [
            types.KeyboardButton(text="Чек-лист"),
            types.KeyboardButton(text="Материалы")
        ],
        [
            types.KeyboardButton(text="Университеты"),
        ],
        [
            types.KeyboardButton(text="Помощь"),
            types.KeyboardButton(text="Язык / тил")
        ],
        [
            types.KeyboardButton(text="Подсчет баллов ОРТ"),
            types.KeyboardButton(text="Профиль"),
            types.KeyboardButton(text="Рассылка"),
            types.KeyboardButton(text="Анонс")
        ],
        [
            types.KeyboardButton(text="Статистика")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="С чего начнем?"
    )
    await message.answer("Что ж, начнем подготовку!", reply_markup=keyboard)

@router.message(F.text.lower() == "материалы")
async def materials_ru(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Математика & Физика",
        url="https://t.me/han_ort_math")
    )
    builder.row(types.InlineKeyboardButton(
        text="Русская грамматика", url="https://t.me/han_ort_rus")
    )
    builder.row(types.InlineKeyboardButton(
        text="Кыргыз грамматикасы", url="https://t.me/han_ort_kg")
    )
    builder.row(types.InlineKeyboardButton(
        text="English",
        url="https://t.me/han_ort_eng")
    )
    builder.row(types.InlineKeyboardButton(
        text="Химия & Биология", url="https://t.me/han_ort_himbio")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - RU", url="https://t.me/han_ort_cloud")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - KG", url="https://t.me/han_jrt_cloud")
    )
    await message.answer("Бесплатные материалы, которые вы искали!", reply_markup=builder.as_markup())

@router.message(F.text.lower() == "материалдар")
async def materials_kg(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Математика & Физика",
        url="https://t.me/han_ort_math")
    )
    builder.row(types.InlineKeyboardButton(
        text="Русская грамматика", url="https://t.me/han_ort_rus")
    )
    builder.row(types.InlineKeyboardButton(
        text="Кыргыз грамматкасы", url="https://t.me/han_ort_kg")
    )
    builder.row(types.InlineKeyboardButton(
        text="English",
        url="https://t.me/han_ort_eng")
    )
    builder.row(types.InlineKeyboardButton(
        text="Химия & Биология", url="https://t.me/han_ort_himbio")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - RU", url="https://t.me/han_ort_cloud")
    )
    builder.row(types.InlineKeyboardButton(
        text="CLOUD - KG", url="https://t.me/han_jrt_cloud")
    )
    await message.answer("Сиз издеген бекер материалдар!", reply_markup=builder.as_markup())

    
@router.message(F.text.lower() == "университеты")
async def ig(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
    text="АУЦА",
    url="https://t.me/studauca"))
    builder.row(types.InlineKeyboardButton(
    text="АЛА-ТОО",
    url="https://t.me/studalatoo"))
    builder.row(types.InlineKeyboardButton(
    text="БГУ",
    url="https://t.me/studbgu"))
    builder.row(types.InlineKeyboardButton(
    text="КНУ & КГЮА",
    url="https://t.me/studknu"))
    builder.row(types.InlineKeyboardButton(
    text="КРСУ",
    url="https://t.me/studkrsu"))
    builder.row(types.InlineKeyboardButton(
    text="МАНАС",
    url="https://t.me/+GcmvEBnMX4MxMDVi"))
    builder.row(types.InlineKeyboardButton(
    text="МУК",
    url="https://t.me/studmuk"))
    builder.row(types.InlineKeyboardButton(
    text="ОШГУ",
    url="https://t.me/+d8FZlWdjmRRlZjZi"))
    builder.row(types.InlineKeyboardButton(
    text="Политех КГТУ",
    url="https://t.me/studkstu"))
    builder.row(types.InlineKeyboardButton(
    text="Медицинские вузы",
    url="https://t.me/studmedkg"))
    
    await message.reply('Университеты:',
    reply_markup=builder.as_markup())

@router.message(F.text.lower() == "университеттер")
async def ig(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
    text="АУЦА",
    url="https://t.me/studauca"))
    builder.row(types.InlineKeyboardButton(
    text="АЛА-ТОО",
    url="https://t.me/studalatoo"))
    builder.row(types.InlineKeyboardButton(
    text="БГУ",
    url="https://t.me/studbgu"))
    builder.row(types.InlineKeyboardButton(
    text="КНУ & КГЮА",
    url="https://t.me/studknu"))
    builder.row(types.InlineKeyboardButton(
    text="КРСУ",
    url="https://t.me/studkrsu"))
    builder.row(types.InlineKeyboardButton(
    text="МАНАС",
    url="https://t.me/+GcmvEBnMX4MxMDVi"))
    builder.row(types.InlineKeyboardButton(
    text="МУК",
    url="https://t.me/studmuk"))
    builder.row(types.InlineKeyboardButton(
    text="ОШГУ",
    url="https://t.me/+d8FZlWdjmRRlZjZi"))
    builder.row(types.InlineKeyboardButton(
    text="Политех КГТУ",
    url="https://t.me/studkstu"))
    builder.row(types.InlineKeyboardButton(
    text="Медициналык жождор",
    url="https://t.me/studmedkg"))
    
    await message.reply('Университеттер:',
    reply_markup=builder.as_markup())


@router.message(F.text.lower() == "чек-лист")
async def checklist(message: Message):
    user_id = message.from_user.id
    lang = await user_lang(user_id)
    if (lang == "ru"):
        await message.reply_document("BQACAgIAAxkBAAIdKGaZQf7AVafCmQdH-nBHWSSVUAwzAAK0PQACtniJS-TGlnduvl9fNQQ", caption="Чек-лист - перечень тем, которые будут на ОРТ. Лишних и отсутствующих тем нет, то есть не нужно изучать то, что не указано в чек-листе")
        await message.answer_document("BQACAgIAAxkBAAIdKmaZQf4uP36Sw3IPeiizu-3FNkXIAAJbNwACF4QQSEYWy3Sk4hxjNQQ", caption="Все формулы по математике основного теста")
    else:
        await message.reply_document("BQACAgIAAxkBAALZr2dciF6699u_aO3yXm-FHn6ZHKJtAAL9PQACtniJS8a7xkayUwcMNgQ", caption="Чек-лист - ЖРТда боло турган темалардын тизмеси. Керексиз же жетишпеген темалар жок, башкача айтканда, чек-листте көрсөтүлбөгөн нерселерди изилдөөнүн кереги жок")
        await message.answer_document("BQACAgIAAxkBAAIdKmaZQf4uP36Sw3IPeiizu-3FNkXIAAJbNwACF4QQSEYWy3Sk4hxjNQQ", caption="Негизги тесттин баардык формулалары")


@router.message(F.text.lower() == "помощь")
@router.message(F.text.lower() == "жардам")
async def ig(message: types.Message):
    user_id = message.from_user.id
    lang = await user_lang(user_id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Telegram",
        url="https://t.me/R_anony"))
    builder.row(types.InlineKeyboardButton(
        text="WhatsApp",
        url="https://wa.me/996700044504"))
    if lang == "kg":
        await message.answer("Курска жазылгыныз келсе же кенеш керек болсо админге жазыныз. (Эгер сизге үй тапшырмасы же башка тапшырма боюнча жардам керек болсо, анда ар бир тапшырма үчүн жардамдын баасы 100 сомдон 1000 сомго чейин)",
        reply_markup=builder.as_markup())
    else:
        await message.answer("Если вы хотите записаться на курс или же нужна консультация, то напишите админу. (Если нужна помощь с домашней работой или любой другой задачей, то помощь стоит от 100 до 1000 сом за каждое задание)",
        reply_markup=builder.as_markup())

@router.message(F.text.lower() == "язык / тил")
@router.message(F.text.lower() == "тил / язык")
async def cmd_lang(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Русский"),
            types.KeyboardButton(text="Кыргызча")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите язык / тил таңданыз"
    )
    await message.answer("Выберите язык, на котором будете сдавать ОРТ\n\nЖРТны тапшыра турган тилди тандаңыз?", reply_markup=keyboard)

@router.message(F.text.lower() == "кыргызча")
async def lang_kg(message: types.Message):
    user_id = message.from_user.id
    await update_user_lang(user_id, "kg")
    await menu_kg(message)


@router.message(F.text.lower() == "русский")
async def lang_kg(message: types.Message):
    user_id = message.from_user.id
    await update_user_lang(user_id, "ru")
    await menu_ru(message)

@router.message(F.text.lower() == "главное меню")
async def main_menu_ru(message: types.Message):
    user_id = message.from_user.id
    await menu_ru(message)

@router.message(F.text.lower() == "башкы меню")
async def main_menu_kg(message: types.Message):
    user_id = message.from_user.id
    await menu_kg(message)
