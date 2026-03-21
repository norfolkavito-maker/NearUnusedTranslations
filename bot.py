import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import (
    start_handler, registration_handler,
    process_epic_id, process_discord,
    on_tier, on_subtier, on_division,
    on_manual_mmr, on_back_to_tiers, on_back_to_subtiers,
    process_rank_mmr_text, process_peak_rank_mmr_text,
    me_handler, list_handler, kick_handler,
)
from db import init_db
from config import TOKEN
from states import Registration
from web import start_web

RANK_STATES = StateFilter(Registration.rank, Registration.peak_rank)


async def main():
    if not TOKEN:
        raise ValueError("TOKEN не задан!")

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()
    await start_web()

    # commands
    dp.message.register(start_handler, Command("start"))
    dp.message.register(list_handler,  Command("list"))
    dp.message.register(me_handler,    Command("me"))
    dp.message.register(kick_handler,  Command("kick"))

    # registration flow
    dp.message.register(registration_handler, F.text == "Регистрация")
    dp.message.register(process_epic_id,  Registration.epic_id)
    dp.message.register(process_discord,  Registration.discord)
    dp.message.register(process_rank_mmr_text,      Registration.rank_mmr)
    dp.message.register(process_peak_rank_mmr_text,  Registration.peak_rank_mmr)

    # rank/peak callbacks (work in both rank and peak_rank states)
    dp.callback_query.register(on_tier,            F.data.startswith("rt:"),  RANK_STATES)
    dp.callback_query.register(on_subtier,         F.data.startswith("rs:"),  RANK_STATES)
    dp.callback_query.register(on_division,        F.data.startswith("rd:"),  RANK_STATES)
    dp.callback_query.register(on_manual_mmr,      F.data.startswith("rm:"),  RANK_STATES)
    dp.callback_query.register(on_back_to_tiers,   F.data.startswith("rb:"),  RANK_STATES)
    dp.callback_query.register(on_back_to_subtiers, F.data.startswith("rsb:"), RANK_STATES)

    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
