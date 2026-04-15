from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import app.keyboards as kb
from .game_core import games, user_game, anonymous_messages, get_user_name


class AnonymousChatStates(StatesGroup):
    waiting_for_message = State()


def register_chat_handlers(router: Router):
    @router.message(F.text == "Анонимный чат")
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
                 f"Вы можете анонимно общаться с вашим подопечным:\n"
                 f"👤 {recipient_name}\n\n"
                 f"Ваш собеседник не узнает, кто отправил сообщение.\n"
                 f"Все сообщения придут ему анонимно.",
            reply_markup=kb.anonymous_chat_menu
        )

    @router.message(F.text == "Написать сообщение")
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
                 f"Сообщение будет отправлено вашему подопечному.\n"
                 f"Он не узнает, кто отправитель.\n\n"
                 f"Напишите текст сообщения:"
        )

    @router.message(AnonymousChatStates.waiting_for_message)
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

    @router.message(F.text == "Просмотреть сообщения")
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