from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
from .game_core import games, user_game, get_user_name


def register_manage_handlers(router: Router):
    @router.message(F.text == "Назад")
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
        budget = game_data.get('budget', "Не указан")

        creator_name = await get_user_name(game_data.get('creator'), bot)

        game_menu_text = f"🎄 ИГРА {game_code} 🎄\n\n"
        game_menu_text += f"👥 Участников: {len(game_data['players'])}\n"
        game_menu_text += f"💰 Бюджет: {budget}\n"
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

    @router.message(F.text == "Удалить игру")
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

    @router.callback_query(lambda c: c.data == "confirm_delete")
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

        for player_id in game_data['players']:
            if player_id in user_game:
                del user_game[player_id]

        del games[game_code]

        await callback.message.edit_text(
            text=f"🗑️ Игра {game_code} успешно удалена!\n\n"
                 f"Было удалено {players_count} участник(ов).\n\n"
                 f"Вы можете создать новую игру в главном меню."
        )

        await callback.message.answer(
            text="Вы вернулись в главное меню",
            reply_markup=kb.main
        )

        await callback.answer()

    @router.callback_query(lambda c: c.data == "cancel_delete")
    async def cancel_delete_game(callback: CallbackQuery):
        await callback.message.edit_text(
            text="❌ Удаление игры отменено.\n\n"
                 "Игра сохранена."
        )
        await callback.answer()