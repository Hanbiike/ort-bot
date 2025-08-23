import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import start, calc, profiles, parser, file_id, tests, creator
from methods import admin, users
from keyboards import menu
from config import BOT_TOKEN
from handlers.parser import poll_news, set_bot
from methods.admin import start_daily_scheduler

# Ensure aiofiles is installed
try:
    import aiofiles
except ImportError:
    print("Installing aiofiles...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiofiles"])
    import aiofiles

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Main function that initializes and starts the bot.
    
    This function sets up the bot, dispatcher, includes all routers,
    starts background tasks, and begins polling for messages.
    """
    bot = Bot(token=BOT_TOKEN)
    #set_bot(bot)
    dp = Dispatcher()
    
    # Include all routers
    dp.include_routers(
        start.router,
        menu.router,
        admin.router,
        users.router,
        calc.router,
        profiles.router,
        tests.router,
        #parser.router,
        file_id.router,
        creator.router
    )
    
    # Start background tasks
    try:
        # Start daily schedule reporter
        scheduler_task = start_daily_scheduler(bot)
        logger.info("Daily scheduler started successfully")
        
        # Schedule poll_news as a background task (when enabled)
        #asyncio.create_task(poll_news())
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise
    finally:
        # Clean up tasks
        if 'scheduler_task' in locals():
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                logger.info("Daily scheduler task cancelled successfully")

if __name__ == "__main__":
    asyncio.run(main())
