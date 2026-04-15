from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
from .game_core import games, user_game, active_game_session, get_user_name


def register_info_handlers(router: Router):
    @router.message(F.text == "Мои игры")
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

    @router.callback_query(lambda c: c.data and c.data.startswith("enter_game_"))
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
        budget = game_data.get('budget', "Не указан")

        creator_name = await get_user_name(game_data.get('creator'), bot)

        game_menu_text = f"🎄 ИГРА {game_code} 🎄\n\n"
        game_menu_text += f"👥 Участников: {len(game_data['players'])}\n"
        game_menu_text += f"💰 Бюджет: {budget}\n"
        game_menu_text += f"👑 Организатор: {creator_name}\n"
        game_menu_text += f"👑 Ваша роль: {'Организатор' if is_organizer else 'Участник'}\n"

        if has_draw:
            game_menu_text += f"🎲 Жеребьёвка: ✅ Проведена\n"
            recipient_id = game_data['draw'].get(user_id)
            if recipient_id:
                recipient_name = await get_user_name(recipient_id, bot)
                game_menu_text += f"🎁 Ваш подопечный: {recipient_name}\n"
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

    @router.message(F.text == "Информация об игре")
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
        budget = game_data.get('budget', "Не указан")

        creator_name = await get_user_name(game_data.get('creator'), bot)

        info_text = f"📊 ИНФОРМАЦИЯ ОБ ИГРЕ 📊\n\n"
        info_text += f"🎮 Код игры: {game_code}\n"
        info_text += f"👥 Участников: {players_count}\n"
        info_text += f"💰 Бюджет подарка: {budget}\n"
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