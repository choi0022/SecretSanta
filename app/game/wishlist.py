from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import app.keyboards as kb
from .core import games, user_game, wishlists, get_user_name


class WishlistStates(StatesGroup):
    waiting_for_wishlist = State()


def register_wishlist_handlers(router: Router):
    @router.message(F.text == "Мой вишлист")
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

    @router.message(WishlistStates.waiting_for_wishlist)
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

    @router.message(F.text == "Узнать кому дарить")
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
                text=f"🎁 Ваш получатель:\n\n"
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