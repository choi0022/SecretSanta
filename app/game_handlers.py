from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import app.keyboards as kb

games = {}
user_game = {}
wishlists = {}
anonymous_messages = {}
active_game_session = {}
user_name_cache = {}

game_router = Router()


class WishlistStates(StatesGroup):
    waiting_for_wishlist = State()


class AnonymousChatStates(StatesGroup):
    waiting_for_message = State()


async def get_user_name(user_id, bot):
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


@game_router.message(F.text == "Главное меню")
async def back_to_main_menu_from_game(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id in active_game_session:
        del active_game_session[user_id]
    await message.answer(
        text='Вы вернулись в главное меню',
        reply_markup=kb.main
    )


@game_router.message(F.text == "Мои игры")
async def my_games(message: Message):
    user_id = message.from_user.id
    from main import bot

    user_games = []
    for code, game_data in games.items():
        if user_id in game_data['players']:
            user_games.append((code, game_data))

    if not user_games:
        await message.answer(
            text="📭 Вы не участвуете ни в одной игре.\n\n"
                 "Создайте новую игру кнопкой «Создать игру»\n"
                 "или присоединитесь к существующей по коду!",
            reply_markup=kb.main
        )
        return

    keyboard = kb.get_games_list_keyboard(user_games, user_id)

    games_text = "🎮 ВАШИ ИГРЫ 🎮\n\n"
    games_text += f"Всего игр: {len(user_games)}\n"
    games_text += f"Всего участников: {sum(len(g['players']) for _, g in user_games)}\n\n"
    games_text += "Нажмите на кнопку с игрой, чтобы войти:"

    await message.answer(
        text=games_text,
        reply_markup=keyboard
    )

    await message.answer(
        text="🏠 Для возврата в главное меню нажмите кнопку ниже:",
        reply_markup=kb.games_list_menu
    )


@game_router.callback_query(lambda c: c.data and c.data.startswith("enter_game_"))
async def enter_game(callback_query: CallbackQuery):
    game_code = callback_query.data.replace("enter_game_", "")
    user_id = callback_query.from_user.id
    from main import bot

    if game_code not in games:
        await callback_query.answer("❌ Игра не найдена!", show_alert=True)
        return

    game_data = games[game_code]

    if user_id not in game_data['players']:
        await callback_query.answer("❌ Вы не участвуете в этой игре!", show_alert=True)
        return

    active_game_session[user_id] = game_code
    user_game[user_id] = game_code

    is_organizer = game_data.get('creator') == user_id
    has_draw = bool(game_data.get('draw'))

    creator_name = await get_user_name(game_data.get('creator'), bot)

    game_menu_text = f"🎄 ИГРА {game_code} 🎄\n\n"
    game_menu_text += f"👥 Участников: {len(game_data['players'])}\n"
    game_menu_text += f"👑 Организатор: {creator_name}\n"
    game_menu_text += f"👑 Ваша роль: {'Организатор' if is_organizer else 'Участник'}\n"

    if has_draw:
        game_menu_text += f"🎲 Жеребьёвка: ✅ Проведена\n"
        recipient_id = game_data['draw'].get(user_id)
        if recipient_id:
            recipient_name = await get_user_name(recipient_id, bot)
            game_menu_text += f"🎁 Ваш получатель: {recipient_name}\n"
    else:
        game_menu_text += f"🎲 Жеребьёвка: ⏳ Не проведена\n"
        if is_organizer:
            game_menu_text += f"⚠️ Нужно участников: {max(0, 3 - len(game_data['players']))}\n"

    await callback_query.message.delete()

    await callback_query.message.answer(
        text=game_menu_text,
        reply_markup=kb.game_menu
    )
    await callback_query.answer(f"Вы вошли в игру {game_code}")


@game_router.message(F.text == "Информация об игре")
async def game_info(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    from main import bot

    if user_id not in user_game:
        await message.answer(
            text="❌ Вы не участвуете ни в одной игре!",
            reply_markup=kb.main
        )
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer("❌ Игра не найдена.")
        return

    players_count = len(game_data['players'])
    is_organizer = game_data.get('creator') == user_id
    has_draw = bool(game_data.get('draw'))
    budget = game_data.get('budget', "Не указан")  # ПОЛУЧАЕМ БЮДЖЕТ

    creator_name = await get_user_name(game_data.get('creator'), bot)

    info_text = f"📊 ИНФОРМАЦИЯ ОБ ИГРЕ 📊\n\n"
    info_text += f"🎮 Код игры: {game_code}\n"
    info_text += f"👥 Участников: {players_count}\n"
    info_text += f"💰 Бюджет подарка: {budget}\n"  # НОВАЯ СТРОКА
    info_text += f"👑 Организатор: {creator_name}\n"
    info_text += f"👑 Ваша роль: {'Организатор' if is_organizer else 'Участник'}\n"

    if players_count >= 3:
        info_text += f"✅ Можно проводить жеребьёвку!\n"
    else:
        info_text += f"⚠️ Нужно еще {3 - players_count} участник(а) для жеребьёвки\n"

    if has_draw:
        info_text += f"🎲 Жеребьёвка: ✅ Проведена\n"
    else:
        info_text += f"🎲 Жеребьёвка: ⏳ Не проведена\n"

    info_text += f"\n📋 Список участников:\n"
    for i, player_id in enumerate(game_data['players'], 1):
        player_name = await get_user_name(player_id, bot)
        role_mark = "👑 " if player_id == game_data.get('creator') else "👤 "
        info_text += f"   {role_mark}{i}. {player_name}\n"

    await message.answer(
        text=info_text,
        reply_markup=kb.info_menu
    )

@game_router.message(F.text == "Провести жеребьёвку")
async def conduct_draw_from_button(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if user_id not in user_game:
        await message.answer(
            text="❌ Вы не участвуете ни в одной игре!",
            reply_markup=kb.main
        )
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer("❌ Игра не найдена!")
        return

    if game_data.get('creator') != user_id:
        await message.answer("❌ Только организатор может проводить жеребьёвку!")
        return

    if game_data.get('draw'):
        await message.answer("⚠️ Жеребьёвка уже была проведена!")
        return

    players_count = len(game_data['players'])

    if players_count < 3:
        await message.answer(
            f"⚠️ Для жеребьёвки нужно минимум 3 участника!\n\n"
            f"Сейчас в игре: {players_count} участник(ов)\n"
            f"Нужно еще: {3 - players_count} участник(а)\n\n"
            f"Пригласите больше участников, отправив им код игры: {game_code}"
        )
        return

    participants = game_data['players'].copy()
    random.shuffle(participants)

    draw_results = {}
    for i in range(len(participants)):
        draw_results[participants[i]] = participants[(i + 1) % len(participants)]

    game_data['draw'] = draw_results
    game_data['status'] = 'completed'

    await message.answer("✅ Жеребьёвка успешно проведена!")

    from main import bot
    for giver_id, receiver_id in draw_results.items():
        try:
            receiver_name = await get_user_name(receiver_id, bot)
            receiver_wishlist = wishlists.get(receiver_id, "Не заполнен")

            message_text = f"🎁 ЖЕРЕБЬЁВКА ЗАВЕРШЕНА! 🎁\n\n"
            message_text += f"Вам выпало подарить подарок: {receiver_name}\n\n"

            if receiver_wishlist:
                message_text += f"📝 Что хочет получить ваш получатель:\n{receiver_wishlist}\n\n"

            message_text += f"🤫 Не раскрывайте свой секрет!\n"
            message_text += f"🎄 Счастливого дарения!"

            await bot.send_message(
                giver_id,
                text=message_text
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {giver_id}: {e}")

    await message.answer(
        text="Жеребьёвка завершена! Теперь вы можете узнать кому дарить подарок.",
        reply_markup=kb.game_menu
    )


@game_router.message(F.text == "Мой вишлист")
async def my_wishlist(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id not in user_game:
        await message.answer(
            text="❌ Вы не участвуете ни в одной игре!",
            reply_markup=kb.main
        )
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer("❌ Игра не найдена!")
        return

    if not game_data.get('draw'):
        current_wishlist = wishlists.get(user_id, "❌ Не заполнен")

        await message.answer(
            text=f"📝 Ваш вишлист\n\n"
                 f"Ваши желания:\n{current_wishlist}\n\n"
                 f"Хотите создать или изменить список желаемых подарков?",
            reply_markup=kb.wishlist_menu
        )
        await state.set_state(WishlistStates.waiting_for_wishlist)
    else:
        recipient_id = game_data['draw'].get(user_id)
        if recipient_id:
            from main import bot
            recipient_name = await get_user_name(recipient_id, bot)
            recipient_wishlist = wishlists.get(recipient_id, "Не заполнен")

            await message.answer(
                text=f"🎁 Вишлист вашего получателя\n\n"
                     f"👤 {recipient_name}\n\n"
                     f"📝 Желаемые подарки:\n{recipient_wishlist}\n\n"
                     f"Вы также можете изменить свой вишлист:",
                reply_markup=kb.wishlist_menu
            )
            await state.set_state(WishlistStates.waiting_for_wishlist)


@game_router.message(WishlistStates.waiting_for_wishlist)
async def save_wishlist(message: Message, state: FSMContext):
    if message.text == "Сохранить вишлист":
        await message.answer("📝 Напишите ваш вишлист (список желаемых подарков):")
        return
    elif message.text == "Отмена":
        await state.clear()
        await message.answer(
            "❌ Редактирование вишлиста отменено",
            reply_markup=kb.info_menu
        )
        return
    elif message.text == "Назад":
        await state.clear()
        await message.answer(
            "Вы вернулись в меню игры",
            reply_markup=kb.info_menu
        )
        return

    user_id = message.from_user.id
    wishlist_text = message.text.strip()

    wishlists[user_id] = wishlist_text

    await message.answer(
        text=f"✅ Ваш вишлист успешно сохранён!\n\n"
             f"📝 Ваши пожелания:\n"
             f"{wishlist_text}\n\n"
             "Теперь ваш Тайный Санта сможет узнать, что вы хотите получить в подарок! 🎄",
        reply_markup=kb.info_menu
    )
    await state.clear()


@game_router.message(F.text == "Узнать кому дарить")
async def know_recipient(message: Message):
    user_id = message.from_user.id
    from main import bot

    if user_id not in user_game:
        await message.answer(
            text="❌ Вы не участвуете ни в одной игре!",
            reply_markup=kb.main
        )
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer("❌ Игра не найдена!")
        return

    if not game_data.get('draw'):
        await message.answer(
            text="🎲 Жеребьёвка ещё не проведена!\n\n"
                 "Дождитесь, пока организатор проведёт жеребьёвку.\n"
                 "После этого вы узнаете, кому нужно дарить подарок.",
            reply_markup=kb.info_menu
        )
        return

    recipient_id = game_data['draw'].get(user_id)
    budget = game_data.get('budget', "Не указан")

    if recipient_id:
        recipient_name = await get_user_name(recipient_id, bot)
        recipient_wishlist = wishlists.get(recipient_id, "Не заполнен")

        await message.answer(
            text=f"🎁 Ваш подопечный:\n\n"
                 f"👤 {recipient_name}\n\n"
                 f"💰 Бюджет подарка: {budget}\n\n"
                 f"📝 Что хочет получить:\n"
                 f"{recipient_wishlist}\n\n"
                 f"🤫 Не раскрывайте свой секрет до вручения подарка!\n"
                 f"🎄 Счастливого дарения!",
            reply_markup=kb.info_menu
        )
    else:
        await message.answer("❌ Ошибка: не удалось определить получателя подарка!")

@game_router.message(F.text == "Анонимный чат")
async def anonymous_chat(message: Message, state: FSMContext):
    user_id = message.from_user.id
    from main import bot

    if user_id not in user_game:
        await message.answer(
            text="❌ Вы не участвуете ни в одной игре!",
            reply_markup=kb.main
        )
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer("❌ Игра не найдена!")
        return

    if not game_data.get('draw'):
        await message.answer(
            text="🎲 Жеребьёвка ещё не проведена!\n\n"
                 "Анонимный чат станет доступен после проведения жеребьёвки.",
            reply_markup=kb.info_menu
        )
        return

    recipient_id = game_data['draw'].get(user_id)

    if not recipient_id:
        await message.answer("❌ Ошибка: не удалось определить получателя!")
        return

    recipient_name = await get_user_name(recipient_id, bot)

    await state.update_data(game_code=game_code, recipient_id=recipient_id)

    await message.answer(
        text=f"💬 Анонимный чат\n\n"
             f"Вы можете анонимно общаться с вашим получателем:\n"
             f"👤 {recipient_name}\n\n"
             f"Ваш собеседник не узнает, кто отправил сообщение.\n"
             f"Все сообщения придут ему анонимно.",
        reply_markup=kb.anonymous_chat_menu
    )


@game_router.message(F.text == "Написать сообщение")
async def send_anonymous_message(message: Message, state: FSMContext):
    data = await state.get_data()
    game_code = data.get('game_code')
    recipient_id = data.get('recipient_id')

    if not game_code or not recipient_id:
        await message.answer("❌ Ошибка! Попробуйте снова.")
        await state.clear()
        return

    await state.set_state(AnonymousChatStates.waiting_for_message)

    await message.answer(
        text=f"💬 Напишите ваше анонимное сообщение\n\n"
             f"Сообщение будет отправлено вашему получателю.\n"
             f"Он не узнает, кто отправитель.\n\n"
             f"Напишите текст сообщения:"
    )


@game_router.message(AnonymousChatStates.waiting_for_message)
async def save_anonymous_message(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.answer(
            "Вы вернулись в анонимный чат",
            reply_markup=kb.anonymous_chat_menu
        )
        return

    user_id = message.from_user.id
    data = await state.get_data()
    game_code = data.get('game_code')
    recipient_id = data.get('recipient_id')
    message_text = message.text.strip()

    if not game_code or not recipient_id:
        await message.answer("❌ Ошибка! Попробуйте снова.")
        await state.clear()
        return

    if game_code not in anonymous_messages:
        anonymous_messages[game_code] = {}

    if recipient_id not in anonymous_messages[game_code]:
        anonymous_messages[game_code][recipient_id] = []

    message_data = {
        'from_user': user_id,
        'text': message_text,
        'timestamp': message.date
    }
    anonymous_messages[game_code][recipient_id].append(message_data)

    try:
        from main import bot
        await bot.send_message(
            recipient_id,
            text=f"💬 Анонимное сообщение от вашего Тайного Санты!\n\n"
                 f"{message_text}\n\n"
                 f"Ответить на это сообщение можно через кнопку «Анонимный чат» в меню."
        )

        await message.answer(
            text="✅ Ваше сообщение отправлено!\n\n"
                 "Получатель получит его анонимно.",
            reply_markup=kb.anonymous_chat_menu
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение: {e}")

    await state.clear()


@game_router.message(F.text == "Просмотреть сообщения")
async def view_messages(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    game_code = data.get('game_code')

    if not game_code:
        game_code = user_game.get(user_id)

    if not game_code or game_code not in games:
        await message.answer("❌ Ошибка! Игра не найдена.")
        return

    messages_list = []
    if game_code in anonymous_messages and user_id in anonymous_messages[game_code]:
        messages_list = anonymous_messages[game_code][user_id]

    if not messages_list:
        await message.answer(
            text="📭 У вас пока нет анонимных сообщений\n\n"
                 "Ваш Тайный Санта может написать вам, чтобы уточнить предпочтения для подарка.",
            reply_markup=kb.anonymous_chat_menu
        )
        return

    messages_text = "💬 Ваши анонимные сообщения 💬\n\n"
    for i, msg in enumerate(messages_list, 1):
        messages_text += f"{i}. {msg['text']}\n\n"

    messages_text += "\n🤫 Отправитель остаётся анонимным!"

    await message.answer(
        text=messages_text,
        reply_markup=kb.anonymous_chat_menu
    )


@game_router.message(F.text == "Назад")
async def back_to_game_menu(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    from main import bot

    if user_id not in user_game:
        await message.answer(
            "Вы вернулись в главное меню",
            reply_markup=kb.main
        )
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer(
            "Вы вернулись в главное меню",
            reply_markup=kb.main
        )
        return

    is_organizer = game_data.get('creator') == user_id
    has_draw = bool(game_data.get('draw'))

    creator_name = await get_user_name(game_data.get('creator'), bot)

    game_menu_text = f"🎄 ИГРА {game_code} 🎄\n\n"
    game_menu_text += f"👥 Участников: {len(game_data['players'])}\n"
    game_menu_text += f"👑 Организатор: {creator_name}\n"
    game_menu_text += f"👑 Ваша роль: {'Организатор' if is_organizer else 'Участник'}\n"

    if has_draw:
        game_menu_text += f"🎲 Жеребьёвка: ✅ Проведена\n"
    else:
        game_menu_text += f"🎲 Жеребьёвка: ⏳ Не проведена\n"

    await message.answer(
        text=game_menu_text,
        reply_markup=kb.game_menu
    )


@game_router.message(F.text == "Удалить игру")
async def delete_game_confirm(message: Message):

    user_id = message.from_user.id

    if user_id not in user_game:
        await message.answer("❌ Вы не участвуете ни в одной игре!")
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await message.answer("❌ Игра не найдена!")
        return

    if game_data.get('creator') != user_id:
        await message.answer("❌ Только организатор может удалить игру!")
        return

    players_count = len(game_data['players'])
    keyboard = kb.get_confirm_delete_keyboard()

    await message.answer(
        text=f"⚠️ ВНИМАНИЕ! ⚠️\n\n"
             f"Вы собираетесь удалить игру {game_code}.\n"
             f"В игре участвует {players_count} человек(а).\n\n"
             f"Все данные будут потеряны безвозвратно!\n\n"
             f"Вы уверены?",
        reply_markup=keyboard
    )


@game_router.callback_query(lambda c: c.data == "confirm_delete")
async def confirm_delete_game(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_game:
        await callback.answer("❌ Вы не участвуете ни в одной игре!", show_alert=True)
        return

    game_code = user_game[user_id]
    game_data = games.get(game_code)

    if not game_data:
        await callback.answer("❌ Игра не найдена!", show_alert=True)
        return

    if game_data.get('creator') != user_id:
        await callback.answer("❌ Только организатор может удалить игру!", show_alert=True)
        return

    players_count = len(game_data['players'])

    # Удаляем игру
    for player_id in game_data['players']:
        if player_id in user_game:
            del user_game[player_id]

    del games[game_code]

    # Редактируем сообщение с подтверждением
    await callback.message.edit_text(
        text=f"🗑️ Игра {game_code} успешно удалена!\n\n"
             f"Было удалено {players_count} участник(ов).\n\n"
             f"Вы можете создать новую игру в главном меню."
    )

    # Отправляем новое сообщение с главным меню
    await callback.message.answer(
        text="Вы вернулись в главное меню",
        reply_markup=kb.main
    )

    await callback.answer()


@game_router.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete_game(callback: CallbackQuery):
    await callback.message.edit_text(
        text="❌ Удаление игры отменено.\n\n"
             "Игра сохранена."
    )
    await callback.answer()