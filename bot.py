import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers import (
    start_handler, registration_handler, sub_check_callback,
    process_epic_id, process_discord,
    on_tier, on_subtier, on_division,
    on_manual_mmr, on_back_to_tiers, on_back_to_subtiers,
    process_rank_mmr_text, process_peak_rank_mmr_text, process_tracker,
    me_handler, admin_panel_handler, admin_callback, admin_kick_id_handler,
    delete_self_handler, delete_self_callback,
    tournament_create_name, tournament_create_description, tournament_create_date,
    tournament_create_players, tournament_create_prize, tournament_list,
    welcome_edit, welcome_view,
    notification_create_tournament_select, notification_create_message, notification_create_time,
    admin_add_id, admin_remove_id, admin_list, admin_manage_id,
    channel_edit_link, channel_view, channel_toggle_subscription, channel_edit_discord,
    contact_admins_handler, discord_handler,
)
from db import init_db
from config import TOKEN
from states import Registration, Admin
from web import start_web
from scheduler import scheduler_task

RANK_STATES = StateFilter(Registration.rank, Registration.peak_rank)


async def main():
    print("🚀 Запуск бота...")
    
    if not TOKEN:
        print("❌ TOKEN не задан!")
        return

    print(f"🔑 TOKEN установлен (длина: {len(TOKEN)})")
    
    try:
        bot = Bot(token=TOKEN)
        print("✅ Bot объект создан")
        
        # Проверяем доступ к боту
        bot_info = await bot.get_me()
        print(f"✅ Бот найден: @{bot_info.username} ({bot_info.first_name})")
        
    except Exception as e:
        print(f"❌ Ошибка создания бота: {e}")
        return

    dp = Dispatcher(storage=MemoryStorage())
    print("✅ Dispatcher создан")
    
    # Initialize database
    try:
        await init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return

    # Register handlers
    try:
        await register_handlers(dp, bot)
        print("✅ Обработчики зарегистрированы")
    except Exception as e:
        print(f"❌ Ошибка регистрации обработчиков: {e}")
        return
    
    # Start web server
    try:
        await start_web()
        print("✅ Веб-сервер запущен")
    except Exception as e:
        print(f"⚠️ Ошибка запуска веб-сервера: {e}")

    print("🚀 Бот запущен, начинаем polling...")
    
    # Start scheduler in background
    try:
        asyncio.create_task(scheduler_task(bot))
        print("✅ Планировщик запущен")
    except Exception as e:
        print(f"⚠️ Ошибка запуска планировщика: {e}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка запуска polling: {e}")
        import traceback
        traceback.print_exc()


async def register_handlers(dp, bot):
    # Commands
    dp.message.register(start_handler, Command("start"))
    dp.message.register(me_handler, F.text == "📋 Мои данные")
    dp.message.register(registration_handler, F.text == "🎮 Регистрация")
    dp.message.register(delete_self_handler, F.text == "🗑 Удалить мои данные")
    dp.message.register(admin_panel_handler, F.text == "⚙️ Админ-панель")

    # subscription recheck
    dp.callback_query.register(sub_check_callback, F.data == "sub_check")

    # rank selection
    dp.callback_query.register(on_tier, F.data.startswith("rt:"))
    dp.callback_query.register(on_subtier, F.data.startswith("rs:"))
    dp.callback_query.register(on_division, F.data.startswith("rd:"))
    dp.callback_query.register(on_back_to_tiers, F.data.startswith("rb:"))
    dp.callback_query.register(on_back_to_subtiers, F.data.startswith("rsb:"))
    dp.callback_query.register(on_manual_mmr, F.data.startswith("rm:"))

    # registration steps
    dp.message.register(process_epic_id, Registration.epic_id)
    dp.message.register(process_discord, Registration.discord)
    dp.callback_query.register(on_tier, StateFilter(Registration.rank, Registration.peak_rank))
    dp.message.register(process_rank_mmr_text, StateFilter(Registration.rank_mmr, Registration.peak_rank_mmr))
    dp.message.register(process_tracker, Registration.tracker)

    # admin panel
    dp.callback_query.register(admin_callback, F.data.startswith("adm:"))
    dp.message.register(admin_kick_id_handler, Admin.waiting_kick_id)

    # self deletion
    dp.callback_query.register(delete_self_callback, F.data.startswith("delete_self:"))

    # tournament management
    dp.callback_query.register(tournament_list, F.data == "tour:list")
    dp.callback_query.register(tournament_create_callback, F.data == "tour:create")
    dp.message.register(tournament_create_name, Admin.waiting_tournament_name)
    dp.message.register(tournament_create_description, Admin.waiting_tournament_description)
    dp.message.register(tournament_create_date, Admin.waiting_tournament_date)
    dp.message.register(tournament_create_players, Admin.waiting_tournament_players)
    dp.message.register(tournament_create_prize, Admin.waiting_tournament_prize)

    # welcome message management
    dp.callback_query.register(welcome_view, F.data == "wel:view")
    dp.callback_query.register(welcome_edit_callback, F.data == "wel:edit")
    dp.message.register(welcome_edit, Admin.waiting_welcome_message)

    # notification management
    dp.callback_query.register(notification_create_tournament_select, F.data == "notif:create")
    dp.message.register(notification_create_message, Admin.waiting_notification_message)
    dp.message.register(notification_create_time, Admin.waiting_notification_time)

    # admin management
    dp.callback_query.register(admin_add_callback, F.data == "admin:add")
    dp.callback_query.register(admin_remove_callback, F.data == "admin:remove")
    dp.callback_query.register(admin_list, F.data == "admin:list")
    dp.message.register(admin_manage_id, Admin.waiting_admin_id)
    
    # channel management
    dp.callback_query.register(channel_edit_callback, F.data == "channel:edit")
    dp.callback_query.register(channel_discord_callback, F.data == "channel:discord")
    dp.callback_query.register(channel_view, F.data == "channel:view")
    dp.callback_query.register(channel_toggle_subscription, F.data == "channel:toggle")
    dp.message.register(channel_edit_link, Admin.waiting_channel_link)
    dp.message.register(channel_edit_discord, Admin.waiting_discord_link)
    
    # user functions
    dp.message.register(contact_admins_handler, F.text == "💬 Обратиться к админам")
    dp.message.register(discord_handler, F.text == "🎮 Discord")


# Admin management callbacks
async def admin_add_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Admin.waiting_admin_id)
    await state.update_data(admin_action="add")

async def admin_remove_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Admin.waiting_admin_id)
    await state.update_data(admin_action="remove")

async def channel_edit_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Admin.waiting_channel_link)

async def channel_discord_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Admin.waiting_discord_link)

async def tournament_create_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Admin.waiting_tournament_name)

async def welcome_edit_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Admin.waiting_welcome_message)


if __name__ == "__main__":
    asyncio.run(main())
# Force Railway cache bust Tue Mar 31 22:00:48 MSK 2026
