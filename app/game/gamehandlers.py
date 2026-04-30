from aiogram import Router
from .core import games, user_game, wishlists, anonymous_messages, active_game_session, user_name_cache, get_user_name, load_all_data
from .info import info
from .draw import draw
from .wishlist import wishlist
from .chat import chat
from .manage import manage

game_router = Router()

info(game_router)
draw(game_router)
wishlist(game_router)
chat(game_router)
manage(game_router)

__all__ = [
    'game_router',
    'games',
    'user_game',
    'wishlists',
    'anonymous_messages',
    'active_game_session',
    'user_name_cache',
    'get_user_name',
    'load_all_data'
]