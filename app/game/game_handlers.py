from aiogram import Router
from .game_core import games, user_game, wishlists, anonymous_messages, active_game_session, user_name_cache, get_user_name
from .game_info import register_info_handlers
from .game_draw import register_draw_handlers
from .game_wishlist import register_wishlist_handlers
from .game_chat import register_chat_handlers
from .game_manage import register_manage_handlers

# Создаём роутер
game_router = Router()

# Регистрируем все обработчики
register_info_handlers(game_router)
register_draw_handlers(game_router)
register_wishlist_handlers(game_router)
register_chat_handlers(game_router)
register_manage_handlers(game_router)

# Экспортируем нужные объекты
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