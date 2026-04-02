from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Создать игру'), KeyboardButton(text='Принять участие')],
        [KeyboardButton(text='Информация об игре'), KeyboardButton(text='Мои игры')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт'
)

game_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Информация об игре')],
        [KeyboardButton(text='Главное меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие'
)

info_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Мой вишлист'), KeyboardButton(text='Узнать кому дарить')],
        [KeyboardButton(text='Анонимный чат'), KeyboardButton(text='Удалить игру')],
        [KeyboardButton(text='Провести жеребьёвку'), KeyboardButton(text='Назад')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие'
)

games_list_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Главное меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Нажмите "Главное меню" для возврата'
)

wishlist_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Сохранить вишлист')],
        [KeyboardButton(text='Отмена'), KeyboardButton(text='Назад')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Напишите ваш вишлист'
)

anonymous_chat_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Написать сообщение')],
        [KeyboardButton(text='Просмотреть сообщения')],
        [KeyboardButton(text='Назад')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие'
)


def get_games_list_keyboard(user_games, user_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for code, game_data in user_games:
        players_count = len(game_data['players'])
        is_organizer = game_data.get('creator') == user_id
        draw_status = "✅" if game_data.get('draw') else "⏳"

        button_text = f"{draw_status} Игра {code} | {players_count} чел"
        if is_organizer:
            button_text += " 👑"

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"enter_game_{code}")
        ])

    return keyboard