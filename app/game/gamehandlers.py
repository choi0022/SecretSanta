from aiogram import Router
from .core import games, user_game, wishlists, anonymous_messages, active_game_session, user_name_cache, get_user_name
from .info import register_info_handlers
from .draw import register_draw_handlers
from .wishlist import register_wishlist_handlers
from .chat import register_chat_handlers
from .manage import register_manage_handlers

game_router = Router()

register_info_handlers(game_router)
register_draw_handlers(game_router)
register_wishlist_handlers(game_router)
register_chat_handlers(game_router)
register_manage_handlers(game_router)

__all__ = [
    'game_router',
    'games',
    'user_game',
    'wishlists',
    'anonymous_messages',
    'active_game_session',
    'user_name_cache',
    'get_user_name'
]