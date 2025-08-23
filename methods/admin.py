from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from dataclasses import dataclass
from typing import Union, List, Dict, Optional, AsyncGenerator, Callable
import asyncio
import json
import logging
import time
import os
from datetime import datetime, timedelta

# Constants
from config import API_TOKEN, GROUPS_FILE, HAN_ID
from methods.admins import is_admin, add_admin, remove_admin, get_all_admins

logger = logging.getLogger(__name__)

@dataclass
class BroadcastStatus:
    total: int = 0
    sent: int = 0
    failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class BroadcastManager:
    def __init__(self, bot: Bot, chunk_size: int = 30, timeout: float = 0.05):
        self.bot = bot
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.status = BroadcastStatus()

    async def _split_messages(self, user_ids: List[int]) -> AsyncGenerator[List[int], None]:
        for i in range(0, len(user_ids), self.chunk_size):
            yield user_ids[i:i + self.chunk_size]

    async def broadcast(self, message_content: 'MessageContent', user_ids: List[int], 
                       progress_callback=None) -> BroadcastStatus:
        self.status = BroadcastStatus(total=len(user_ids), start_time=datetime.now())

        async for chunk in self._split_messages(user_ids):
            try:
                tasks = [message_content.send(self.bot, uid) for uid in chunk]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        self.status.failed += 1
                    else:
                        self.status.sent += 1

                if progress_callback:
                    await progress_callback(self.status)

                await asyncio.sleep(self.timeout)

            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)

        self.status.end_time = datetime.now()
        return self.status

class MessageContent:
    def __init__(self, content: Union[str, Dict[str, str]]):
        self.content = content
        self.is_photo = isinstance(content, dict) and 'photo' in content

    async def send(self, bot: Bot, chat_id: int) -> bool:
        try:
            if self.is_photo:
                await bot.send_photo(
                    chat_id,
                    self.content['photo'],
                    caption=self.content.get('caption', ''),
                    parse_mode='HTML'
                )
            else:
                await bot.send_message(
                    chat_id, 
                    self.content,
                    parse_mode='HTML'
                )
            return True
        except Exception as e:
            logger.error(f"Error sending to {chat_id}: {e}")
            return False

async def broadcast_to_groups(content: MessageContent, group_ids: List[int], pin_option: str, progress_callback=None) -> BroadcastStatus:
    status = BroadcastStatus(total=len(group_ids), start_time=datetime.now())
    for gid in group_ids:
        try:
            msg = await content.send(bot, gid)
            if pin_option in ["pin_with_notification", "pin_without_notification"] and isinstance(msg, types.Message):
                await bot.pin_chat_message(gid, msg.message_id, disable_notification=(pin_option=="pin_without_notification"))
            status.sent += 1
        except Exception as e:
            logger.error(f"Error sending to group {gid}: {e}")
            status.failed += 1
        if progress_callback:
            await progress_callback(status)
        await asyncio.sleep(0.05)
    status.end_time = datetime.now()
    return status

class Cache:
    def __init__(self, ttl_seconds: int = 300):
        self._data: Dict = {}
        self._ttl = ttl_seconds
        self._timestamps: Dict = {}

    def get(self, key: str) -> Optional[any]:
        if key not in self._timestamps:
            return None
        
        if time.time() - self._timestamps[key] > self._ttl:
            del self._data[key]
            del self._timestamps[key]
            return None
            
        return self._data.get(key)

    def set(self, key: str, value: any) -> None:
        self._data[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        self._data.clear()
        self._timestamps.clear()

class States(StatesGroup):
    waiting_for_content = State()
    confirmation = State()
    choose_target = State()
    pin_option = State()
    final_confirmation = State()
    waiting_for_admin_id = State()    # New state for admin management

bot = Bot(token=API_TOKEN)
router = Router()
storage = MemoryStorage()
cache = Cache()
broadcast_manager = BroadcastManager(bot)

def load_groups() -> List[int]:
    groups = cache.get('groups')
    if groups is not None:
        return groups

    try:
        with open(GROUPS_FILE, 'r') as file:
            groups = [int(line.strip()) for line in file]
            cache.set('groups', groups)
            return groups
    except Exception as e:
        logger.error(f"Error reading groups: {e}")
        return []


@router.message(F.text.lower() == "сезам откройся")
async def add_group_id(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    group_id = message.chat.id
    groups = set(load_groups())
    if group_id in groups:
        await message.reply("Группа уже добавлена.")
        return

    try:
        with open(GROUPS_FILE, "a") as file:
            file.write(f"{group_id}\n")
        cache.clear()
        await message.reply("Группа добавлена в список рассылки.")
    except Exception as e:
        logger.error(f"Error adding group: {e}")
        await message.reply("Не удалось добавить группу.")

@router.message(F.text.lower().in_(["рассылка", "анонс"]))
async def start_process(message: types.Message, state: FSMContext):
    # Check if user is admin
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
        
    await state.set_state(States.waiting_for_content)
    await message.answer("Ожидаю сообщение или изображение")

@router.message(States.waiting_for_content, F.content_type.in_(['text', 'photo']))
async def handle_content(message: types.Message, state: FSMContext):
    content = (
        message.html_text
        if message.content_type == 'text'
        else {"photo": message.photo[-1].file_id, "caption": message.html_text or ""}
    )

    await state.update_data(content=content)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Да", callback_data="confirm"))
    builder.add(types.InlineKeyboardButton(text="Нет", callback_data="cancel"))

    if message.content_type == 'photo':
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=message.html_text or None,
            parse_mode='HTML'
        )
    else:
        await message.answer(message.html_text, parse_mode='HTML')

    await message.answer(
        "Подтвердите отправку?",
        reply_markup=builder.as_markup()
    )
    
    await state.set_state(States.confirmation)

@router.callback_query(States.confirmation)
async def process_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'cancel':
        await state.clear()
        await callback_query.message.answer("Отменено.")
        return

    data = await state.get_data()
    content = MessageContent(data.get('content'))

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(
        text="Только в группах",
        callback_data="target_groups"
    ))
    keyboard.add(types.InlineKeyboardButton(
        text="Всем пользователям",
        callback_data="target_all"
    ))

    await callback_query.message.answer(
        "Кому отправить сообщение?",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(States.choose_target)


@router.callback_query(States.choose_target)
async def process_target(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data not in ["target_groups", "target_all"]:
        await callback_query.answer()
        return

    await state.update_data(target=callback_query.data)

    if callback_query.data == "target_groups":
        keyboard = InlineKeyboardBuilder()
        keyboard.add(types.InlineKeyboardButton(
            text="С закреплением",
            callback_data="pin_with_notification"
        ))
        keyboard.add(types.InlineKeyboardButton(
            text="Без закрепления",
            callback_data="pin_without_notification"
        ))

        await callback_query.message.answer(
            "Закрепить сообщение?",
            reply_markup=keyboard.as_markup()
        )
        await state.set_state(States.pin_option)
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(types.InlineKeyboardButton(text="Начать", callback_data="start"))
        keyboard.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))

        await callback_query.message.answer(
            "Начать рассылку всем пользователям?",
            reply_markup=keyboard.as_markup()
        )
        await state.set_state(States.final_confirmation)


@router.callback_query(States.pin_option)
async def process_pin_option(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data not in ["pin_with_notification", "pin_without_notification"]:
        await callback_query.answer()
        return

    await state.update_data(pin_option=callback_query.data)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text="Начать", callback_data="start"))
    keyboard.add(types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))

    await callback_query.message.answer(
        "Подтвердите рассылку в группах?",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(States.final_confirmation)


@router.callback_query(States.final_confirmation)
async def process_final_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "cancel":
        await state.clear()
        await callback_query.message.answer("Отменено.")
        return

    data = await state.get_data()
    content = MessageContent(data.get('content'))
    target = data.get('target')

    if target == "target_groups":
        group_ids = load_groups()
        status_message = await callback_query.message.answer(
            f"Начинаю рассылку в {len(group_ids)} группах..."
        )

        async def progress_callback(status: BroadcastStatus):
            await status_message.edit_text(
                f"Отправлено: {status.sent}/{status.total}\n"
                f"Ошибок: {status.failed}"
            )

        final_status = await broadcast_to_groups(
            content,
            group_ids,
            data.get('pin_option', "pin_without_notification"),
            progress_callback,
        )

    else:
        try:
            with open('schedule.json', 'r') as file:
                schedule_data = json.load(file)
                user_ids = [info["user_id"] for info in schedule_data.values()]
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            await callback_query.message.answer("Ошибка загрузки пользователей")
            await state.clear()
            return

        status_message = await callback_query.message.answer(
            f"Начинаю рассылку {len(user_ids)} пользователям..."
        )

        async def progress_callback(status: BroadcastStatus):
            await status_message.edit_text(
                f"Отправлено: {status.sent}/{status.total}\n"
                f"Ошибок: {status.failed}"
            )

        final_status = await broadcast_manager.broadcast(
            content,
            user_ids,
            progress_callback,
        )

    duration = final_status.end_time - final_status.start_time
    await callback_query.message.answer(
        f"Рассылка завершена за {duration.seconds} сек.\n"
        f"Успешно: {final_status.sent}\n"
        f"Ошибок: {final_status.failed}"
    )
    await state.clear()

# Admin management commands
@router.message(Command("add_admin"))
async def cmd_add_admin(message: types.Message, state: FSMContext):
    # Only main admin can add admins
    if message.from_user.id != HAN_ID:
        await message.answer("Только главный администратор может добавлять других администраторов.")
        return
        
    await message.answer("Отправьте ID пользователя, которого хотите сделать администратором.")
    await state.set_state(States.waiting_for_admin_id)
    await state.update_data(action="add")

@router.message(Command("remove_admin"))
async def cmd_remove_admin(message: types.Message, state: FSMContext):
    # Only main admin can remove admins
    if message.from_user.id != HAN_ID:
        await message.answer("Только главный администратор может удалять других администраторов.")
        return
        
    await message.answer("Отправьте ID пользователя, которого хотите удалить из администраторов.")
    await state.set_state(States.waiting_for_admin_id)
    await state.update_data(action="remove")

@router.message(Command("list_admins"))
async def cmd_list_admins(message: types.Message):
    # Only admins can see the admin list
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
        
    admins = get_all_admins()
    if not admins:
        await message.answer("Список администраторов пуст.")
        return
        
    admin_text = "Список администраторов:\n"
    for admin_id in admins:
        admin_text += f"- {admin_id}\n"
        
    await message.answer(admin_text)

@router.message(States.waiting_for_admin_id)
async def process_admin_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        data = await state.get_data()
        action = data.get("action")
        
        if action == "add":
            if add_admin(user_id):
                await message.answer(f"Пользователь с ID {user_id} успешно добавлен как администратор.")
            else:
                await message.answer(f"Пользователь с ID {user_id} уже является администратором.")
        elif action == "remove":
            if user_id == HAN_ID:
                await message.answer("Невозможно удалить главного администратора.")
            elif remove_admin(user_id):
                await message.answer(f"Пользователь с ID {user_id} успешно удален из администраторов.")
            else:
                await message.answer(f"Пользователь с ID {user_id} не является администратором.")
    except ValueError:
        await message.answer("Пожалуйста, отправьте корректный ID пользователя (число).")
    finally:
        await state.clear()

async def send_daily_schedule_report(bot: Bot) -> None:
    """
    Send the daily schedule.json file to the bot owner.
    
    This function reads the schedule.json file and sends it to the owner
    with a detailed report about the current user base statistics.
    
    Args:
        bot (Bot): The aiogram Bot instance used for sending messages
        
    Raises:
        Exception: If there's an error reading or sending the file
    """
    try:
        schedule_file_path = 'schedule.json'
        
        # Check if schedule file exists
        if not os.path.exists(schedule_file_path):
            logger.warning("Schedule file not found for daily report")
            await bot.send_message(
                HAN_ID,
                "📋 Ежедневный отчет: файл schedule.json не найден"
            )
            return
            
        # Get file statistics
        file_size = os.path.getsize(schedule_file_path)
        modification_time = datetime.fromtimestamp(
            os.path.getmtime(schedule_file_path)
        )
        
        # Load and analyze schedule data
        try:
            with open(schedule_file_path, 'r', encoding='utf-8') as file:
                schedule_data = json.load(file)
                user_count = len(schedule_data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Error reading schedule file content: {e}")
            user_count = "Неизвестно"
            schedule_data = {}
        
        # Create detailed report caption
        caption = (
            f"📋 Ежедневный отчет - schedule.json\n"
            f"📅 Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"👥 Пользователей в базе: {user_count}\n"
            f"📦 Размер файла: {file_size} байт\n"
            f"🕒 Последнее изменение: {modification_time.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Send the file with detailed information
        with open(schedule_file_path, 'rb') as file:
            await bot.send_document(
                chat_id=HAN_ID,
                document=types.FSInputFile(
                    schedule_file_path, 
                    filename=f'schedule_{datetime.now().strftime("%Y%m%d")}.json'
                ),
                caption=caption
            )
            
        logger.info(f"Daily schedule report sent successfully to {HAN_ID}")
        
    except Exception as e:
        logger.error(f"Error sending daily schedule report: {e}")
        try:
            await bot.send_message(
                HAN_ID,
                f"❌ Ошибка отправки ежедневного отчета: {str(e)}"
            )
        except Exception as send_error:
            logger.error(f"Failed to send error notification: {send_error}")


async def daily_schedule_task(bot: Bot) -> None:
    """
    Background task that schedules daily sending of schedule.json.
    
    This function runs continuously and triggers the daily report
    sending at 9:00 AM each day. It handles errors gracefully and
    reschedules itself for the next day.
    
    Args:
        bot (Bot): The aiogram Bot instance
        
    Note:
        This function runs indefinitely and should be started as
        a background task using asyncio.create_task()
    """
    while True:
        try:
            now = datetime.now()
            
            # Set target time to 9:00 AM today
            target_time = now.replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            
            # If it's already past 9 AM today, schedule for tomorrow
            if now >= target_time:
                target_time += timedelta(days=1)
            
            # Calculate seconds until target time
            time_until_target = (target_time - now).total_seconds()
            
            logger.info(
                f"Next daily schedule report scheduled for: "
                f"{target_time.strftime('%d.%m.%Y %H:%M')}"
            )
            
            # Wait until target time
            await asyncio.sleep(time_until_target)
            
            # Send the daily report
            await send_daily_schedule_report(bot)
            
        except asyncio.CancelledError:
            logger.info("Daily schedule task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in daily schedule task: {e}")
            # Wait 1 hour before retrying if there's an error
            await asyncio.sleep(3600)


def start_daily_scheduler(bot: Bot) -> asyncio.Task:
    """
    Initialize and start the daily scheduler as a background task.
    
    This function creates a background task for the daily schedule
    reporting and returns the task handle for potential cancellation.
    
    Args:
        bot (Bot): The aiogram Bot instance
        
    Returns:
        asyncio.Task: The created task handle
        
    Example:
        scheduler_task = start_daily_scheduler(bot)
        # Later, if needed:
        # scheduler_task.cancel()
    """
    task = asyncio.create_task(daily_schedule_task(bot))
    logger.info("Daily schedule reporter started successfully")
    return task

@router.message(Command("send_schedule"))
async def cmd_send_schedule_now(message: types.Message) -> None:
    """
    Manually trigger the sending of schedule.json file.
    
    This command allows the main administrator to manually request
    the schedule file at any time, useful for testing or immediate needs.
    
    Args:
        message (types.Message): The command message from the user
    """
    if message.from_user.id != HAN_ID:
        await message.answer(
            "Только главный администратор может использовать эту команду."
        )
        return
        
    await message.answer("📋 Отправляю файл schedule.json...")
    await send_daily_schedule_report(bot)
    await message.answer("✅ Файл отправлен!")
