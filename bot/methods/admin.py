from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from dataclasses import dataclass
from typing import Union, List, Dict, Optional, AsyncGenerator
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta

# Constants
from ..config import API_TOKEN, GROUPS_FILE, HAN_ID, DATA_FILE
from .admins import is_admin, add_admin, remove_admin, get_all_admins

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
    pin_option = State()
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

@router.message(F.text.lower().in_(["рассылка", "анонс"]))
async def start_process(message: types.Message, state: FSMContext):
    # Check if user is admin
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
        
    await state.update_data(mode=message.text.lower())
    await state.set_state(States.waiting_for_content)
    await message.answer("Ожидаю сообщение или изображение")

@router.message(States.waiting_for_content, F.content_type.in_(['text', 'photo']))
async def handle_content(message: types.Message, state: FSMContext):
    content = (message.html_text if message.content_type == 'text'
              else {"photo": message.photo[-1].file_id, "caption": message.html_text if message.caption else ""})
    
    await state.update_data(content=content)
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Да", callback_data="confirm"))
    builder.add(types.InlineKeyboardButton(text="Нет", callback_data="cancel"))

    preview = ("📝 Текст:\n\n" + message.html_text) if message.content_type == 'text' else (
        "🖼 Фото" + ("\n\n📝 Подпись:\n" + message.html_text if message.caption else " (без подписи)")
    )
    
    if message.content_type == 'photo':
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=f"⬆️ Предпросмотр\n\n{preview}",
            parse_mode='HTML'
        )
    
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
    mode = data.get('mode')
    content = MessageContent(data.get('content'))

    if mode == 'анонс':
        keyboard = InlineKeyboardBuilder()
        keyboard.add(types.InlineKeyboardButton(
            text="Закрепить с уведомлением", 
            callback_data="pin_with_notification"
        ))
        keyboard.add(types.InlineKeyboardButton(
            text="Закрепить без звука", 
            callback_data="pin_without_notification"
        ))
        keyboard.add(types.InlineKeyboardButton(
            text="Не закреплять", 
            callback_data="do_not_pin"
        ))
        
        await callback_query.message.answer(
            "Выберите опцию закрепления:",
            reply_markup=keyboard.as_markup()
        )
        await state.set_state(States.pin_option)
        return

    # Regular broadcast
    try:
        with open(DATA_FILE, 'r') as file:
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
        progress_callback
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

# ...remaining handlers...
