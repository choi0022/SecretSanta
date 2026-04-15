from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import app.keyboards as kb

# Словари для хранения данных
games = {}
user_game = {}
wishlists = {}
anonymous_messages = {}
active_game_session = {}
user_name_cache = {}


async def get_user_name(user_id, bot):
    """Получает имя пользователя по его ID"""
    if user_id in user_name_cache:
        return user_name_cache[user_id]

    try:
        user = await bot.get_chat(user_id)
        if user.first_name:
            if user.last_name:
                name = f"{user.first_name} {user.last_name}"
            else:
                name = user.first_name
        else:
            name = f"User_{user_id}"

        user_name_cache[user_id] = name
        return name
    except:
        return f"User_{user_id}"