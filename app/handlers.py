from aiogram import types, F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import random

import app.keyboards as kb
from app.game.gamehandlers import game_router, games, user_game

router = Router()

router.include_router(game_router)


class GameStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_budget = State()


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

    await state.update_data(game_code=code)
    await state.set_state(GameStates.waiting_for_budget)

    await message.answer(
        text=f"🎄 Создание игры\n\n"
             f"Код игры: {code}\n\n"
             f"Установите бюджет подарка (в рублях):\n"
             f"Например: 1000-2000, до 1500, от 500, 1000\n\n"
             f"Или напишите 'пропустить', если хотите без ограничений",
        reply_markup=kb.budget_menu
    )


@router.message(GameStates.waiting_for_budget)
async def set_budget(message: Message, state: FSMContext):
    budget_text = message.text.strip()
    data = await state.get_data()
    game_code = data.get('game_code')

    if budget_text.lower() == "пропустить":
        budget = "Не указан"
    else:
        budget = budget_text

    games[game_code] = {
        "players": [message.from_user.id],
        "draw": {},
        "status": "waiting",
        "creator": message.from_user.id,
        "budget": budget
    }
    user_game[message.from_user.id] = game_code

    await state.clear()

    await message.answer(
        text=f"✅ Игра успешно создана!\n\n"
             f"👑 Вы стали организатором игры.\n"
             f"🎮 Код игры: {game_code}\n"
             f"💰 Бюджет подарка: {budget}\n\n"
             f"Отправьте этот код другим участникам,\n"
             f"чтобы они могли присоединиться к игре",
        reply_markup=kb.game_menu
    )


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