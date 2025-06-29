import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio
from aiogram import Bot, Dispatcher
from bot.handlers import start, calc, profiles, parser
from bot.methods import admin, users
from bot.keyboards import menu
from bot.config import BOT_TOKEN
from bot.handlers.parser import poll_news, set_bot

async def main():
    bot = Bot(token=BOT_TOKEN)
    set_bot(bot)
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        menu.router,
        admin.router,
        users.router,
        calc.router,
        profiles.router,
        parser.router
    )
    # Schedule poll_news as a background task
    asyncio.create_task(poll_news())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
