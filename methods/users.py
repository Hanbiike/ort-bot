import json
import datetime
import logging
import re
import asyncio
from functools import lru_cache
from aiogram import Router, F, types, Bot
from config import BOT_TOKEN, OWNER_ID, GROUP_ID, DATA_FILE
from methods.utils import read_json_file, write_json_file

bot = Bot(token=BOT_TOKEN)
router = Router()

# Moderation settings
MUTE_DURATION = datetime.timedelta(weeks=1)
CACHE_DURATION = 300  # 5 minutes cache for admin status

# Utility function to read data from JSON file
def read_data():
    return read_json_file(DATA_FILE, default_data={})

# Utility function to write data to JSON file
def write_data(data):
    write_json_file(DATA_FILE, data)

# Function to find user data by user_id
def find_user_data(user_id):
    data = read_data()
    return data.get(str(user_id))

# Function to update user data
def update_user_data(user):
    data = read_data()
    data[str(user['user_id'])] = user
    write_data(data)

async def user_data(user_id: int):
    user = find_user_data(user_id)
    if not user:
        user = {'user_id': user_id, 'lang': 'ru', 'sub': 0, 'expire_date': None}
        update_user_data(user)
    return user

async def user_lang(user_id: int):
    try:
        user = await user_data(user_id)
        return user['lang']
    except Exception as e:
        logging.error(f"Error getting user language: {e}")
        return "ru"  # Return default language in case of error

async def user_sub(user_id: int):
    try:
        user = await user_data(user_id)
        return user['sub']
    except Exception as e:
        logging.error(f"Error getting user subscription status: {e}")
        return 0  # Return default sub in case of error

async def user_date(user_id: int, short: bool = False):
    try:
        user = await user_data(user_id)
        date = datetime.datetime.fromisoformat(user['expire_date']) if user['expire_date'] else datetime.datetime.now() - datetime.timedelta(seconds=1)
        return date.strftime("%Y-%m-%d %H:%M") if short else date
    except Exception as e:
        logging.error(f"Error getting user expiration date: {e}")
        return datetime.datetime.now()  # Return current time in case of error

async def update_user_sub(user_id: int, expiry_time: datetime, trial: bool, link: str):
    try:
        user = await user_data(user_id)
        user['expire_date'] = expiry_time.isoformat()
        user['trial'] = int(trial)
        user['link'] = link
        user['sub'] = int(not trial)
        update_user_data(user)
    except Exception as e:
        logging.error(f"Error updating user subscription: {e}")

async def update_user_lang(user_id, lang):
    try:
        user = await user_data(user_id)
        user['lang'] = lang
        update_user_data(user)
    except Exception as e:
        logging.error(f"Error updating user language: {e}")

async def all_users():
    try:
        data = read_data()
        return [int(user_id) for user_id in data]
    except Exception as e:
        logging.error(f"Error getting all users: {e}")
        return []

# Process the ban/kick process
async def remove_user(user_id):
    try:
        await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
        logging.info(f"User {user_id} removed from group {GROUP_ID}")
        await bot.send_message(chat_id=OWNER_ID, text=f"❌ <b>REMOVED</b>: <a href='tg://user?id={user_id}'>{user_id}</a> from group.", parse_mode="HTML")
        await bot.send_message(chat_id=user_id, text=f"❌ <b>LICENSE EXPIRED</b>", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed to remove user {user_id} from group {GROUP_ID}: {e}")

    data = read_data()
    if str(user_id) in data:
        del data[str(user_id)]
        write_data(data)

# On start verifies expired memberships
async def load_jobs():
    data = read_data()
    now = datetime.datetime.now()
    for user_id, job_data in data.items():
        removal_date = datetime.datetime.fromisoformat(job_data['expire_date']) if job_data['expire_date'] else now
        if removal_date < now:
            await remove_user(int(user_id))

@lru_cache(maxsize=100, typed=True)
async def is_admin(user_id: int, chat_id: int):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.is_chat_admin()
    except Exception as e:
        logging.error(f"Error checking admin status: {user_id} in {chat_id}: {e}")
        return False

@router.message(F.entities.as_("entities"))
@router.message(F.caption_entities.as_("entities"))
async def moderate_message(message: types.Message, entities: list):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Skip moderation for admins, bot, owner, and Telegram service accounts
        if (await is_admin(user_id, chat_id) or 
            user_id == bot.id or 
            user_id == OWNER_ID or
            user_id in [777000, 1087968824] or  # Telegram and GroupAnonymousBot
            message.from_user.is_bot):  # Skip all bots
            return

        # Check only for URLs in entities
        has_links = any(
            entity.type in ['url', 'text_link']  # Only check for actual links
            for entity in (entities or [])
        )
        
        if has_links:
            # Delete message
            await message.delete()
            
            # Mute user
            mute_until = datetime.datetime.now() + MUTE_DURATION
            await message.chat.restrict(
                user_id=user_id,
                permissions=types.ChatPermissions(can_send_messages=False),
                until_date=mute_until
            )
            
            # Notify about mute
            notification = (
                f"🚫 Пользователь {message.from_user.mention_html()} заблокирован "
                f"на {MUTE_DURATION.days} дней за отправку ссылки."
            )
            await message.answer(notification, parse_mode="HTML")
            
            logging.info(
                f"Moderated: User {user_id} in chat {chat_id}. "
                f"Reason: link detection"
            )
            
    except Exception as e:
        logging.error(f"Moderation error: {e}")

# Optimize statistics collection
async def get_statistics():
    try:
        data = read_data()
        total_users = len(data)
        active_users = 0
        
        # Process users in batches to avoid rate limits
        batch_size = 20
        for i in range(0, total_users, batch_size):
            batch = list(data.keys())[i:i + batch_size]
            for user_id in batch:
                try:
                    await bot.send_chat_action(int(user_id), 'typing')
                    active_users += 1
                except:
                    continue
                await asyncio.sleep(0.05)  # Prevent rate limiting
                
        return {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': total_users - active_users
        }
    except Exception as e:
        logging.error(f"Statistics error: {e}")
        return {'total_users': 0, 'active_users': 0, 'blocked_users': 0}

@router.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
        
    stats = await get_statistics()
    await message.answer(
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"✅ Активных: {stats['active_users']}\n"
        f"❌ Заблокировали бота: {stats['blocked_users']}\n",
        parse_mode="HTML"
    )
