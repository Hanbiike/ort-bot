import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, calc, profiles, parser, file_id, tests
from methods import admin, users
from keyboards import menu
from config import BOT_TOKEN
from handlers.parser import poll_news, set_bot

async def main():
    bot = Bot(token=BOT_TOKEN)
    #set_bot(bot)
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        menu.router,
        admin.router,
        users.router,
        calc.router,
        profiles.router,
        tests.router,
        #parser.router,
        file_id.router
    )
    # Schedule poll_news as a background task
    #asyncio.create_task(poll_news())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
