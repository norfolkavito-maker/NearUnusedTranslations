import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import (
    start_handler, registration_handler, sub_check_callback,
    process_epic_id, process_discord,
    on_tier, on_subtier, on_division,
    on_manual_mmr, on_back_to_tiers, on_back_to_subtiers,
    process_rank_mmr_text, process_peak_rank_mmr_text, process_tracker,
    me_handler, admin_panel_handler, admin_callback, admin_kick_id_handler,
)
from db import init_db
from config import TOKEN
from states import Registration, Admin
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
    dp.message.register(me_handler,    Command("me"))

    # buttons
    dp.message.register(registration_handler, F.text == "🎮 Регистрация")
    dp.message.register(me_handler,           F.text == "📋 Мои данные")
    dp.message.register(admin_panel_handler,  F.text == "⚙️ Админ-панель")

    # registration flow
    dp.message.register(process_epic_id,           Registration.epic_id)
    dp.message.register(process_discord,           Registration.discord)
    dp.message.register(process_rank_mmr_text,      Registration.rank_mmr)
    dp.message.register(process_peak_rank_mmr_text, Registration.peak_rank_mmr)
    dp.message.register(process_tracker,            Registration.tracker)

    # rank selection callbacks
    dp.callback_query.register(on_tier,             F.data.startswith("rt:"),  RANK_STATES)
    dp.callback_query.register(on_subtier,          F.data.startswith("rs:"),  RANK_STATES)
    dp.callback_query.register(on_division,         F.data.startswith("rd:"),  RANK_STATES)
    dp.callback_query.register(on_manual_mmr,       F.data.startswith("rm:"),  RANK_STATES)
    dp.callback_query.register(on_back_to_tiers,    F.data.startswith("rb:"),  RANK_STATES)
    dp.callback_query.register(on_back_to_subtiers, F.data.startswith("rsb:"), RANK_STATES)

    # subscription recheck
    dp.callback_query.register(sub_check_callback, F.data == "sub_check")

    # admin panel
    dp.callback_query.register(admin_callback, F.data.startswith("adm:"))
    dp.message.register(admin_kick_id_handler, Admin.waiting_kick_id)

    print("Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
