from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import random
import app.keyboards as kb
from .core import games, user_game, wishlists, active_game_session, get_user_name
import database as db

def draw(router: Router):
    @router.message(F.text == "Провести жеребьёвку")
    async def draw_button(message: Message, state: FSMContext):
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

        db.update_game_draw(game_code, draw_results)

        await message.answer("✅ Жеребьёвка успешно проведена!")

        from main import bot
        for giver_id, receiver_id in draw_results.items():
            try:
                receiver_name = await get_user_name(receiver_id, bot)
                receiver_wishlist = wishlists.get(receiver_id, "Не заполнен")
                budget = game_data.get('budget', "Не указан")

                message_text = f"🎁 ЖЕРЕБЬЁВКА ЗАВЕРШЕНА! 🎁\n\n"
                message_text += f"Вам выпало подарить подарок: {receiver_name}\n"
                message_text += f"💰 Бюджет: {budget}\n\n"

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