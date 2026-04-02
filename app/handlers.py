from aiogram import types, F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import random

import app.keyboards as kb
from app.game_handlers import games, user_game, game_router

router = Router()

router.include_router(game_router)


class GameStates(StatesGroup):
    waiting_for_code = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text='Добро пожаловать в Тайный Санта 🎄',
        reply_markup=kb.main)


@router.message(F.text == "Создать игру")
async def create_game(message: Message, state: FSMContext):
    await state.clear()
    code = str(random.randint(10000, 99999))
    games[code] = {
        "players": [message.from_user.id],
        "draw": {},
        "status": "waiting",
        "creator": message.from_user.id
    }
    user_game[message.from_user.id] = code
    await message.answer(
        text=f"Игра успешно создана!\n\n"
             f"Вы стали организатором игры.\n"
             f"Код игры: {code}\n\n"
             f"Отправьте этот код другим участникам,\n"
             f"чтобы они могли присоединиться к игре",
        reply_markup=kb.game_menu)


@router.message(F.text == "Правила игры")
async def rules(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"""
ПРАВИЛА ИГРЫ «ТАЙНЫЙ САНТА»

1. Организатор создаёт игру и получает уникальный код
2. Участники присоединяются к игре, введя этот код
3. Когда все зарегистрированы, организатор запускает жеребьёвку
4. Каждый участник получает имя человека, которому он должен подарить подарок
5. Личность дарителя остаётся секретом до вручения подарка

Минимум 3 участника для проведения жеребьёвки

Приятной игры! 🎉""")


@router.message(F.text == "Принять участие")
async def join(message: Message, state: FSMContext):
    await state.set_state(GameStates.waiting_for_code)
    await message.answer("🔑 Введите код игры (5 цифр):")


@router.message(GameStates.waiting_for_code)
async def join_code(message: Message, state: FSMContext):
    code = message.text.strip()

    if not code.isdigit() or len(code) != 5:
        await message.answer("❌ Код должен состоять из 5 цифр. Попробуйте еще раз:")
        return

    if code in games:
        if message.from_user.id in games[code]['players']:
            await message.answer("❌ Вы уже присоединились к этой игре!")
            await state.clear()
            return

        games[code]['players'].append(message.from_user.id)
        user_game[message.from_user.id] = code

        await message.answer(
            text=f"✅ Вы присоединились к игре!\nКод игры: {code}",
            reply_markup=kb.game_menu
        )
        await state.clear()
    else:
        await message.answer("❌ Неверный код игры. Попробуйте еще раз:")


@router.message(F.text == "Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text='Вы вернулись в главное меню',
        reply_markup=kb.main
    )