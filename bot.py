import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import (
    start_handler,
    registration_handler,
    process_epic_id,
    process_discord,
    process_rank_callback,
    process_peak_rank_callback,
    me_handler,
    list_handler,
    kick_handler,
)
from db import init_db
from config import TOKEN
from states import Registration
from web import start_web


async def main():
    if not TOKEN:
        raise ValueError("TOKEN не задан! Добавь его в секреты (переменная TOKEN).")

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()
    await start_web()

    dp.message.register(start_handler, Command(commands=["start"]))
    dp.message.register(list_handler, Command(commands=["list"]))
    dp.message.register(me_handler, Command(commands=["me"]))
    dp.message.register(kick_handler, Command(commands=["kick"]))
    dp.message.register(registration_handler, F.text == "Регистрация")
    dp.message.register(process_epic_id, Registration.epic_id)
    dp.message.register(process_discord, Registration.discord)

    dp.callback_query.register(process_rank_callback, F.data.startswith("rank:"), Registration.rank)
    dp.callback_query.register(process_peak_rank_callback, F.data.startswith("peak:"), Registration.peak_rank)

    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
