import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, calc, profiles  # Add this import
from methods import admin, users
from keyboards import menu
from config import BOT_TOKEN

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        menu.router,
        admin.router,
        users.router,
        calc.router,
        profiles.router  # Add this line
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
