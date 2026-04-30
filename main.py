import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from app.handlers import router
from app.game.gamehandlers import load_all_data

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    await load_all_data()
    print("✅ Данные загружены из базы данных")

    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())