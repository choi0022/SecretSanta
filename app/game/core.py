from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import app.keyboards as kb
import database as db

games = {}
user_game = {}
wishlists = {}
anonymous_messages = {}
active_game_session = {}
user_name_cache = {}


async def load_all_data():
    global games, wishlists, anonymous_messages, user_name_cache
    games_dict = db.get_all_games()
    games.clear()
    games.update(games_dict)

    for code, game_data in games.items():
        players = db.get_players(code)
        game_data['players'] = [p['user_id'] for p in players]

        creator_id = db.get_game_creator(code)
        if creator_id:
            game_data['creator'] = creator_id

        draw_data = db.get_game(code)
        if draw_data and draw_data.get('draw'):
            game_data['draw'] = draw_data['draw']

        for p in players:
            if p['wishlist']:
                wishlists[p['user_id']] = p['wishlist']

    for code, game_data in games.items():
        creator_id = game_data.get('creator')
        if creator_id:
            cached_name = db.get_user_name_from_cache(creator_id)
            if cached_name:
                user_name_cache[creator_id] = cached_name

        for player_id in game_data.get('players', []):
            if player_id not in user_name_cache:
                cached_name = db.get_user_name_from_cache(player_id)
                if cached_name:
                    user_name_cache[player_id] = cached_name

async def get_user_name(user_id, bot):
    if not user_id:
        return "Неизвестный"

    if user_id in user_name_cache and user_name_cache[user_id] != "None" and user_name_cache[user_id]:
        return user_name_cache[user_id]

    cached_name = db.get_user_name_from_cache(user_id)
    if cached_name and cached_name != "None":
        user_name_cache[user_id] = cached_name
        return cached_name

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
        db.save_user_name(user_id, name)
        return name
    except Exception as e:
        print(f"Ошибка получения имени для {user_id}: {e}")
        return f"User_{user_id}"