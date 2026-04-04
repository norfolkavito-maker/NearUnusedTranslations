import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.dispatcher.middlewares.base import BaseMiddleware

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
    notification_create_tournament_select, notification_tournament_selected, notification_create_message, notification_create_time,
    broadcast_start, broadcast_send,
    admin_list, admin_manage_id,
    channel_edit_link, channel_view, channel_toggle_subscription, channel_edit_discord,
    contact_admins_handler, contact_admins_message_handler, discord_handler,
    superuser_command, superuser_password_handler, superuser_callback, superuser_new_password_handler,
    superuser_restore_handler,
    post_reg_message_edit,
    post_reg_edit_callback, post_reg_view_callback,
    my_data_edit_callback, my_data_back_callback, my_data_edit_handler,
)
from db import init_db, add_admin, get_pending_notifications
from config import TOKEN
from states import Registration, Admin, SuperUser, ContactAdmin, MyData
from web import start_web
from scheduler import scheduler_task

RANK_STATES = StateFilter(Registration.rank, Registration.peak_rank)


class CallbackLoggerMiddleware(BaseMiddleware):
    """Middleware для логирования всех callback_query"""
    async def __call__(self, handler, event, data):
        try:
            user = event.from_user
            print(f"📞 CALLBACK: user={user.id} (@{user.username or 'no_username'}) data={event.data}")
        except Exception as e:
            print(f"⚠️ Error logging callback: {e}")
        return await handler(event, data)


async def main():
    print("🚀 Запуск бота...")
    
    if not TOKEN:
        print("❌ TOKEN не установлен!")
        return
    
    print(f"🔑 TOKEN установлен (длина: {len(TOKEN)})")
    
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)
    
    try:
        # Удаляем webhook чтобы избежать конфликта с polling
        await bot.delete_webhook()
        print("✅ Webhook удалён")
        
        me = await bot.get_me()
        print(f"✅ Бот найден: @{me.username} ({me.full_name})")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Сначала инициализируем БД, потом всё остальное
    try:
        await init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Критическая ошибка инициализации БД: {e}")
        return
    
    # Register callback logger middleware
    dp.callback_query.middleware(CallbackLoggerMiddleware())
    print("📝 Middleware логирования зарегистрирован")
    
    register_handlers(dp)
    print("✅ Обработчики зарегистрированы")
    
    # Запускаем фоновые задачи
    asyncio.create_task(start_web())
    print("🌐 Веб-панель запущена на порту 5000")
    
    asyncio.create_task(scheduler_task(bot))
    print("✅ Планировщик запущен")
    
    # Один polling вызов, без конфликтов
    print("🚀 Бот запущен, начинаем polling...")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )


def register_handlers(dp: Dispatcher):
    from keyboards import (
        kb_admin_panel, kb_users_menu, kb_messages_menu, kb_settings_menu,
        kb_tournament_menu, kb_welcome_menu, kb_post_reg_menu, kb_notifications_menu,
        kb_channel_menu, kb_admin_menu,
    )
    
    # Basic commands
    dp.message.register(start_handler, Command("start"))
    dp.message.register(registration_handler, F.text == "🎮 Регистрация")
    dp.message.register(me_handler, F.text == "📋 Мои данные")
    dp.message.register(delete_self_handler, F.text == "🗑 Удалить мои данные")
    dp.message.register(discord_handler, F.text == "💬 Discord / TG чат")
    
    # Admin panel
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
    dp.message.register(process_rank_mmr_text, Registration.rank_mmr)
    dp.message.register(process_peak_rank_mmr_text, Registration.peak_rank_mmr)
    dp.message.register(process_tracker, Registration.tracker)
    
    # admin panel
    dp.callback_query.register(admin_callback, F.data.startswith("adm:"))
    dp.message.register(admin_kick_id_handler, Admin.waiting_kick_id)
    
    # self deletion
    dp.callback_query.register(delete_self_callback, F.data.startswith("delete_self:"))
    
    # tournament management
    dp.callback_query.register(tournament_list, F.data == "tour:list")
    dp.callback_query.register(tournament_create_callback, F.data == "tour:create")
    dp.callback_query.register(tournament_notifications_callback, F.data == "tour:notifications")
    
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
    dp.callback_query.register(notification_tournament_selected, F.data.startswith("notif:tour:"))
    dp.callback_query.register(pending_notifications_callback, F.data == "notif:list")
    dp.callback_query.register(broadcast_start, F.data == "notif:broadcast")
    dp.message.register(notification_create_message, Admin.waiting_notification_message)
    dp.message.register(notification_create_time, Admin.waiting_notification_time)
    dp.message.register(broadcast_send, Admin.waiting_broadcast_message)
    
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
    
    # superuser
    dp.message.register(superuser_command, Command("superuser"))
    dp.message.register(superuser_password_handler, SuperUser.waiting_password)
    dp.message.register(superuser_new_password_handler, SuperUser.waiting_new_password)
    dp.callback_query.register(superuser_callback, F.data.startswith("su:"))
    
    # contact admins
    dp.message.register(contact_admins_handler, F.text == "📨 Обратиться к админам")
    dp.message.register(contact_admins_message_handler, ContactAdmin.waiting_message)
    
    # post registration message
    dp.message.register(post_reg_message_edit, Admin.waiting_post_reg_message)
    
    # my data editing
    dp.callback_query.register(my_data_edit_callback, F.data.startswith("mydata:edit_"))
    dp.callback_query.register(my_data_back_callback, F.data == "mydata:back")
    dp.message.register(my_data_edit_handler, MyData.waiting_epic, MyData.waiting_discord, MyData.waiting_rank, MyData.waiting_peak_rank, MyData.waiting_tracker)
    
    # post-registration message management
    dp.callback_query.register(post_reg_edit_callback, F.data == "postreg:edit")
    dp.callback_query.register(post_reg_view_callback, F.data == "postreg:view")


# Admin management callbacks
async def admin_add_callback(callback: CallbackQuery, state: FSMContext):
    print(f"🎯 Кнопка 'Добавить админа' нажата!")
    await callback.answer("Выбрано: Добавить админа")
    await state.set_state(Admin.waiting_admin_id)
    await state.update_data(admin_action="add")
    await callback.message.answer("📝 Введите ID пользователя для добавления в админы:")

async def admin_remove_callback(callback: CallbackQuery, state: FSMContext):
    print(f"🎯 Кнопка 'Удалить админа' нажата!")
    await callback.answer("Выбрано: Удалить админа")
    await state.set_state(Admin.waiting_admin_id)
    await state.update_data(admin_action="remove")
    await callback.message.answer("📝 Введите ID пользователя для удаления из админов:")

# Tournament notifications callback
async def tournament_notifications_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🔔 <b>Уведомления турниров</b>\n\n"
        "📢 Выберите действие:",
        reply_markup=kb_notifications_menu,
        parse_mode="HTML"
    )

# Tournament create callback
async def tournament_create_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Создание нового турнира")
    await callback.message.edit_text(
        "🏆 <b>Создание турнира</b>\n\n"
        "Введите название турнира:",
        parse_mode="HTML"
    )
    await state.set_state(Admin.waiting_tournament_name)

# Pending notifications list callback
async def pending_notifications_callback(callback: CallbackQuery):
    from db import get_pending_notifications
    from keyboards import kb_admin_panel
    notifications = await get_pending_notifications()
    
    if not notifications:
        await callback.message.edit_text(
            "📋 <b>Отложенные рассылки:</b>\n\nНет запланированных рассылок",
            reply_markup=kb_admin_panel,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = "📋 <b>Отложенные рассылки:</b>\n\n"
    for notif in notifications:
        text += f"🏆 Турнир ID: {notif['tournament_id']}\n"
        text += f"⏰ Время: {notif['send_time']}\n"
        text += f"📝 Сообщение: {notif['message'][:50]}...\n\n"
    
    await callback.message.edit_text(text, reply_markup=kb_admin_panel, parse_mode="HTML")
    await callback.answer()

async def channel_edit_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Режим редактирования ссылки канала")
    await callback.message.edit_text(
        "📢 <b>Изменение ссылки канала</b>\n\n"
        "Введите новую ссылку на канал (например: https://t.me/ebka_news):",
        parse_mode="HTML"
    )
    await state.set_state(Admin.waiting_channel_link)

async def channel_discord_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Режим редактирования Discord ссылки")
    await callback.message.edit_text(
        "🎮 <b>Изменение Discord ссылки</b>\n\n"
        "Введите новую ссылку на Discord (например: https://discord.gg/xxxxx):",
        parse_mode="HTML"
    )
    await state.set_state(Admin.waiting_discord_link)

async def welcome_edit_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Режим редактирования приветствия")
    await callback.message.edit_text(
        "📝 <b>Изменение приветственного сообщения</b>\n\n"
        "Введите новый текст приветствия (поддерживается HTML):",
        parse_mode="HTML"
    )
    await state.set_state(Admin.waiting_welcome_message)


if __name__ == "__main__":
    asyncio.run(main())