# Fixed: 2026-04-03 11:33 MSK - syntax error fix
from aiogram import types, Bot, F
from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from db import (
    add_user, check_user, get_user, get_all_users, delete_user, delete_all_users, count_users,
    add_admin, remove_admin, get_all_admins, is_admin_db,
    update_channel_settings, get_channel_settings,
    add_tournament, get_all_tournaments, get_tournament, update_tournament, delete_tournament,
    add_welcome_message, get_active_welcome_message, update_welcome_message,
    add_tournament_notification, get_pending_notifications, mark_notification_sent,
    get_superuser_password, set_superuser_password,
    log_activity, get_activity_logs, clear_activity_logs,
    log_bot, get_bot_logs, clear_bot_logs,
    create_backup, restore_from_backup, get_backup_count,
)
from states import Registration, Admin, ContactAdmin, SuperUser
from keyboards import (
    kb_main, kb_admin_main, kb_tiers, kb_subtiers, kb_divisions,
    kb_sub_check, kb_admin_panel, kb_deleteall_confirm, kb_delete_confirm,
    kb_admin_menu, kb_tournament_menu, kb_welcome_menu, kb_notifications_menu, kb_channel_menu,
    kb_superuser_main, kb_superuser_back, kb_clear_logs_confirm,
    TIERS, get_rank_label, get_auto_mmr, get_mmr_range,
)
from config import CHANNEL_ID, CHANNEL_LINK, GROUP_LINK, ADMIN_IDS


def is_admin(user_id: int) -> bool:
    # Check config admins first
    if user_id in ADMIN_IDS:
        return True
    # Check database admins
    return is_admin_db(user_id)


def _main_kb(user_id: int):
    return kb_admin_main if is_admin(user_id) else kb_main


# ── /start ───────────────────────────────────────────────────────────────────
async def start_handler(msg: types.Message):
    # Get custom welcome message
    welcome = await get_active_welcome_message()
    welcome_text = welcome["message"] if welcome else (
        "👋 Привет! Нажми <b>🎮 Регистрация</b> чтобы участвовать в турнире.\n"
        "Команда <b>📋 Мои данные</b> покажет твою анкету."
    )
    
    await msg.answer(
        welcome_text,
        reply_markup=_main_kb(msg.from_user.id),
        parse_mode="HTML"
    )


# ── Регистрация ──────────────────────────────────────────────────────────────
async def registration_handler(msg: types.Message, state: FSMContext, bot: Bot):
    tg_id = msg.from_user.id
    if await check_user(tg_id):
        await msg.answer("✅ Ты уже зарегистрирован! Используй <b>📋 Мои данные</b> чтобы посмотреть анкету.", parse_mode="HTML")
        return

    try:
        member = await bot.get_chat_member(CHANNEL_ID, tg_id)
        if member.status in ["left", "kicked"]:
            await msg.answer(
                f"⛔ Чтобы зарегистрироваться нужно подписаться на канал{' и вступить в группу' if GROUP_LINK else ''}.",
                reply_markup=kb_sub_check(CHANNEL_LINK, GROUP_LINK)
            )
            return
    except Exception:
        pass

    await _start_registration(msg)
    await state.set_state(Registration.epic_id)


async def _start_registration(msg: types.Message):
    await msg.answer(
        "📝 <b>Регистрация</b>\n\n"
        "1️⃣ Введи свой <b>Epic ID</b>:",
        parse_mode="HTML"
    )


# ── Callback: повторная проверка подписки ────────────────────────────────────
async def sub_check_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    tg_id = callback.from_user.id
    if await check_user(tg_id):
        await callback.message.edit_text("✅ Ты уже зарегистрирован!")
        try:
            await callback.answer()
        except Exception as e:
            print(f"⚠️ Ошибка ответа на callback: {e}")
        return

    try:
        member = await bot.get_chat_member(CHANNEL_ID, tg_id)
        subscribed = member.status not in ["left", "kicked"]
    except Exception:
        subscribed = True

    if not subscribed:
        try:
            await callback.answer("❌ Ты ещё не подписался!", show_alert=True)
        except Exception as e:
            print(f"⚠️ Ошибка ответа на callback: {e}")
        return

    await callback.message.edit_text("✅ Подписка подтверждена!")
    await _start_registration(callback.message)
    await state.set_state(Registration.epic_id)
    try:
        await callback.answer()
    except Exception as e:
        print(f"⚠️ Ошибка ответа на callback: {e}")


# ── Шаги регистрации ─────────────────────────────────────────────────────────
async def process_epic_id(msg: types.Message, state: FSMContext):
    await state.update_data(epic=msg.text)
    await msg.answer("2️⃣ Введи свой <b>Discord</b> (например User#1234):", parse_mode="HTML")
    await state.set_state(Registration.discord)


async def process_discord(msg: types.Message, state: FSMContext):
    await state.update_data(discord=msg.text)
    await msg.answer(
        "3️⃣ Выбери свой <b>актуальный MMR</b>:",
        reply_markup=kb_tiers("r"),
        parse_mode="HTML"
    )
    await state.set_state(Registration.rank)


# ── Выбор тира ───────────────────────────────────────────────────────────────
async def on_tier(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str = callback.data.split(":")
    tier_idx = int(tier_idx_str)
    tier_name = TIERS[tier_idx][1]
    
    await callback.message.edit_text(
        f"Выбери подтир <b>{tier_name}</b>:",
        reply_markup=kb_subtiers(prefix, tier_idx),
        parse_mode="HTML"
    )
    await callback.answer()


async def on_subtier(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str, sub_str = callback.data.split(":")
    tier_idx = int(tier_idx_str)
    sub = int(sub_str)
    tier_name = TIERS[tier_idx][1]
    
    await callback.message.edit_text(
        f"Выбери дивизион для <b>{tier_name} {sub}</b>:",
        reply_markup=kb_divisions(prefix, tier_idx, sub),
        parse_mode="HTML"
    )
    await callback.answer()


async def on_division(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str, sub_str, div_str = callback.data.split(":")
    tier_idx, sub, div = int(tier_idx_str), int(sub_str), int(div_str)
    rank_label = get_rank_label(tier_idx, sub, div)
    mmr = get_auto_mmr(tier_idx, sub, div)
    rank_value = f"{rank_label} ({mmr} MMR)"

    if prefix == "r":
        await state.update_data(rank=rank_value)
        await callback.message.edit_text(
            f"✅ Актуальный MMR: <b>{rank_label}</b> — {mmr} MMR\n\n"
            f"<b>Теперь выберите свой пиковый MMR:</b>",
            reply_markup=kb_tiers("p"),
            parse_mode="HTML"
        )
        await state.set_state(Registration.peak_rank)
    else:
        await state.update_data(peak_rank=rank_value)
        await callback.message.edit_text(
            f"✅ Пиковый MMR: <b>{rank_label}</b> — {mmr} MMR\n\n"
            f"5️⃣ Вставь ссылку на свой <b>RL Tracker</b>:\n"
            f"<i>Пример: https://rocketleague.tracker.network/rocket-league/profile/epic/НикнеймTRN/overview</i>",
            parse_mode="HTML"
        )
        await state.set_state(Registration.tracker)
    await callback.answer()


async def on_manual_mmr(callback: CallbackQuery, state: FSMContext):
    _, prefix = callback.data.split(":")
    label = "актуальный" if prefix == "r" else "пиковый"
    await callback.message.edit_text(
        f"✏️ Введи свой <b>{label} MMR</b> числом (например: 1450):",
        parse_mode="HTML"
    )
    await state.set_state(Registration.rank_mmr if prefix == "r" else Registration.peak_rank_mmr)
    await callback.answer()


async def on_back_to_tiers(callback: CallbackQuery, state: FSMContext):
    _, prefix = callback.data.split(":")
    label = "актуальный" if prefix == "r" else "пиковый"
    step = "3️⃣" if prefix == "r" else "4️⃣"
    await callback.message.edit_text(
        f"{step} Выбери свой <b>{label} MMR</b>:",
        reply_markup=kb_tiers(prefix),
        parse_mode="HTML"
    )
    await callback.answer()


async def on_back_to_subtiers(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str = callback.data.split(":")
    tier_idx = int(tier_idx_str)
    step = "3️⃣" if prefix == "r" else "4️⃣"
    await callback.message.edit_text(
        f"{step} Выбери <b>{TIERS[tier_idx][1]}</b> 1, 2 или 3:",
        reply_markup=kb_subtiers(prefix, tier_idx),
        parse_mode="HTML"
    )
    await callback.answer()


async def process_rank_mmr_text(msg: types.Message, state: FSMContext):
    try:
        mmr = int(msg.text.strip())
        if not 0 <= mmr <= 10000:
            raise ValueError
    except ValueError:
        await msg.answer("⚠️ Введи корректное число MMR, например: 1450")
        return
    await state.update_data(rank=f"MMR: {mmr}")
    await msg.answer(
        f"✅ Актуальный MMR: <b>{mmr}</b>\n\n4️⃣ Теперь выбери свой <b>пиковый MMR</b>:",
        reply_markup=kb_tiers("p"),
        parse_mode="HTML"
    )
    await state.set_state(Registration.peak_rank)


async def process_peak_rank_mmr_text(msg: types.Message, state: FSMContext):
    try:
        mmr = int(msg.text.strip())
        if not 0 <= mmr <= 10000:
            raise ValueError
    except ValueError:
        await msg.answer("⚠️ Введи корректное число MMR, например: 2700")
        return
    await state.update_data(peak_rank=f"MMR: {mmr}")
    await msg.answer(
        f"✅ Пиковый MMR: <b>{mmr}</b>\n\n"
        f"5️⃣ Вставь ссылку на свой <b>RL Tracker</b>:\n"
        f"<i>Пример: https://rocketleague.tracker.network/rocket-league/profile/epic/НикнеймTRN/overview</i>",
        parse_mode="HTML"
    )
    await state.set_state(Registration.tracker)


async def process_tracker(msg: types.Message, state: FSMContext):
    url = msg.text.strip()
    if not url.startswith("http"):
        await msg.answer(
            "⚠️ Вставь корректную ссылку, начинающуюся с <b>https://</b>\n"
            "<i>Пример: https://rocketleague.tracker.network/rocket-league/profile/epic/НикнеймTRN/overview</i>",
            parse_mode="HTML"
        )
        return
    await state.update_data(tracker=url)
    data = await state.get_data()
    tg_id = msg.from_user.id
    username = _get_username(msg.from_user)
    await add_user(
        tg_id=tg_id, username=username,
        epic=data.get("epic", ""), discord=data.get("discord", ""),
        rank=data.get("rank", ""), peak_rank=data.get("peak_rank", ""),
        tracker=url
    )
    await state.clear()
    await msg.answer(
        "🎉 <b>Ты успешно зарегистрирован!</b> Ожидай начала турнира.",
        parse_mode="HTML"
    )


# ── Helpers ──────────────────────────────────────────────────────────────────
def _get_username(user) -> str:
    return f"@{user.username}" if user.username else user.full_name


async def _save_and_finish(callback: CallbackQuery, state: FSMContext, peak_rank: str):
    data = await state.get_data()
    await add_user(
        tg_id=callback.from_user.id, username=_get_username(callback.from_user),
        epic=data.get("epic", ""), discord=data.get("discord", ""),
        rank=data.get("rank", ""), peak_rank=peak_rank
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ Пиковый MMR: <b>{peak_rank}</b>\n\n"
        f"🎉 <b>Ты успешно зарегистрирован!</b> Ожидай начала турнира.",
        parse_mode="HTML"
    )


async def _save_and_finish_msg(msg: types.Message, state: FSMContext, peak_rank: str):
    data = await state.get_data()
    await add_user(
        tg_id=msg.from_user.id, username=_get_username(msg.from_user),
        epic=data.get("epic", ""), discord=data.get("discord", ""),
        rank=data.get("rank", ""), peak_rank=peak_rank
    )
    await state.clear()
    await msg.answer(
        f"✅ Пиковый MMR: <b>{peak_rank}</b>\n\n"
        f"🎉 <b>Ты успешно зарегистрирован!</b> Ожидай начала турнира.",
        parse_mode="HTML"
    )


# ── /me ──────────────────────────────────────────────────────────────────────
async def me_handler(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user:
        await msg.answer("❌ Ты не зарегистрирован. Нажми <b>🎮 Регистрация</b>.", parse_mode="HTML")
        return
    tracker = user.get("tracker") or "—"
    tracker_line = f'5️⃣ RL Tracker: <a href="{tracker}">открыть</a>' if tracker != "—" else "5️⃣ RL Tracker: —"
    await msg.answer(
        f"📋 <b>Твоя анкета:</b>\n\n"
        f"1️⃣ Epic ID: <b>{user['epic']}</b>\n"
        f"2️⃣ Discord: <b>{user['discord']}</b>\n"
        f"3️⃣ Актуальный MMR: <b>{user['rank']}</b>\n"
        f"4️⃣ Пиковый MMR: <b>{user['peak_rank']}</b>\n"
        f"{tracker_line}",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# ── Админ-панель ─────────────────────────────────────────────────────────────
async def admin_panel_handler(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    count = await count_users()
    await msg.answer(
        f"⚙️ <b>Админ-панель</b>\n👥 Участников: <b>{count}</b>",
        reply_markup=kb_admin_panel,
        parse_mode="HTML"
    )


async def admin_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    action = callback.data.split(":")[1]

    if action == "list":
        users = await get_all_users()
        if not users:
            await callback.message.edit_text("⚙️ Никто ещё не зарегистрировался.", reply_markup=kb_admin_panel)
            await callback.answer()
            return
        text = f"👥 <b>Участники ({len(users)}):</b>\n\n"
        for i, u in enumerate(users, 1):
            text += (
                f"{i}. {u.get('username','—')} | <code>{u['tg_id']}</code>\n"
                f"   Epic: {u['epic']} | Discord: {u['discord']}\n"
                f"   MMR: {u['rank']} | Пик: {u['peak_rank']}\n\n"
            )
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            await callback.message.answer(chunk, parse_mode="HTML")
        await callback.answer()

    elif action == "stats":
        users = await get_all_users()
        count = len(users)
        await callback.message.edit_text(
            f"📊 <b>Статистика:</b>\n👥 Зарегистрировано: <b>{count}</b> игроков",
            reply_markup=kb_admin_panel,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "tournaments":
        await callback.message.edit_text(
            "🏆 <b>Управление турнирами:</b>",
            reply_markup=kb_tournament_menu,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "welcome":
        await callback.message.edit_text(
            "📝 <b>Приветственное сообщение:</b>",
            reply_markup=kb_welcome_menu,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "notifications":
        await callback.message.edit_text(
            "📢 <b>Управление рассылками:</b>",
            reply_markup=kb_notifications_menu,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "players":
        users = await get_all_users()
        if not users:
            await callback.message.edit_text("👥 <b>Зарегистрированных игроков пока нет</b>", reply_markup=kb_admin_panel, parse_mode="HTML")
            await callback.answer()
            return
        
        # Создаем красивый список
        text = f"👥 <b>Зарегистрированные игроки ({len(users)}):</b>\n\n"
        
        for i, user in enumerate(users, 1):
            username = user.get('username', 'Без username')
            epic = user.get('epic', 'Не указан')
            discord = user.get('discord', 'Не указан')
            rank = user.get('rank', 'Не указан')
            peak_rank = user.get('peak_rank', 'Не указан')
            tracker = user.get('tracker', 'Не указан')
            
            text += f"🎮 <b>{i}. @{username}</b> (<code>{user['tg_id']}</code>)\n"
            text += f"   🎯 Epic: <b>{epic}</b>\n"
            text += f"   💬 Discord: <b>{discord}</b>\n"
            text += f"   🏆 Ранг: <b>{rank}</b> | Пик: <b>{peak_rank}</b>\n"
            text += f"   📊 Tracker: <b>{tracker}</b>\n\n"
        
        # Разбиваем на части если слишком длинное сообщение
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            try:
                await callback.message.edit_text(chunk, parse_mode="HTML")
            except:
                await callback.message.answer(chunk, parse_mode="HTML")
        
        await callback.answer()

    elif action == "admins":
        await callback.message.edit_text(
            "👥 <b>Управление админами:</b>",
            reply_markup=kb_admin_menu,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "channel":
        await callback.message.edit_text(
            "📢 <b>Настройки канала:</b>",
            reply_markup=kb_channel_menu,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "back":
        count = await count_users()
        await callback.message.edit_text(
            f"⚙️ <b>Админ-панель</b>\n👥 Участников: <b>{count}</b>",
            reply_markup=kb_admin_panel,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "kick":
        await callback.message.edit_text(
            "🗑 Введи <b>Telegram ID</b> игрока которого хочешь удалить:",
            parse_mode="HTML"
        )
        await state.set_state(Admin.waiting_kick_id)
        await callback.answer()

    elif action == "deleteall":
        count = await count_users()
        await callback.message.edit_text(
            f"⚠️ <b>Удалить всех {count} участников?</b>\nЭто действие необратимо!",
            reply_markup=kb_deleteall_confirm,
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "deleteall_yes":
        await delete_all_users()
        await callback.message.edit_text(
            "💥 <b>Все участники удалены.</b>",
            reply_markup=kb_admin_panel,
            parse_mode="HTML"
        )
        await callback.answer("Готово!")

    elif action == "cancel":
        count = await count_users()
        await callback.message.edit_text(
            f"⚙️ <b>Админ-панель</b>\n👥 Участников: <b>{count}</b>",
            reply_markup=kb_admin_panel,
            parse_mode="HTML"
        )
        await callback.answer("Отменено")


async def admin_kick_id_handler(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    try:
        tg_id = int(msg.text.strip())
    except ValueError:
        await msg.answer("⚠️ Введи корректный Telegram ID (только цифры).")
        return

    if not await check_user(tg_id):
        await msg.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    await delete_user(tg_id)
    await state.clear()
    await msg.answer(f"✅ Пользователь <code>{tg_id}</code> удалён.", parse_mode="HTML",
                     reply_markup=_main_kb(msg.from_user.id))


# ── Удаление своих данных ───────────────────────────────────────────────────────
async def delete_self_handler(msg: types.Message):
    if not await check_user(msg.from_user.id):
        await msg.answer("❌ Ты не зарегистрирован. Нажми <b>🎮 Регистрация</b>.", parse_mode="HTML")
        return
    
    await msg.answer(
        "⚠️ <b>Удалить все твои данные?</b>\n"
        "Это действие нельзя будет отменить.",
        reply_markup=kb_delete_confirm,
        parse_mode="HTML"
    )


async def delete_self_callback(callback: CallbackQuery):
    if callback.data == "delete_self:yes":
        tg_id = callback.from_user.id
        await delete_user(tg_id)
        await callback.message.edit_text(
            "✅ <b>Твои данные удалены.</b>\n"
            "Если захочешь снова участвовать, нажми <b>🎮 Регистрация</b>.",
            parse_mode="HTML"
        )
        await callback.answer("Данные удалены")
    else:
        await callback.message.edit_text(
            "❌ Отмена. Твои данные сохранены.",
            parse_mode="HTML"
        )
        await callback.answer("Отменено")


# ── Tournament Management ───────────────────────────────────────────────────────
async def tournament_create_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("📝 Введи описание турнира:")
    await state.set_state(Admin.waiting_tournament_description)

async def tournament_create_description(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer("📅 Введи дату и время турнира (формат: YYYY-MM-DD HH:MM):")
    await state.set_state(Admin.waiting_tournament_date)

async def tournament_create_date(msg: types.Message, state: FSMContext):
    await state.update_data(date_time=msg.text)
    await msg.answer("👥 Введи максимальное количество игроков (или пропусти):")
    await state.set_state(Admin.waiting_tournament_players)

async def tournament_create_players(msg: types.Message, state: FSMContext):
    if msg.text.strip():
        try:
            max_players = int(msg.text)
            await state.update_data(max_players=max_players)
        except ValueError:
            await msg.answer("⚠️ Введи корректное число или отправь /skip для пропуска")
            return
    await msg.answer("🏆 Введи призовой фонд (или пропусти):")
    await state.set_state(Admin.waiting_tournament_prize)

async def tournament_create_prize(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    prize = msg.text if msg.text.strip() else None
    
    await add_tournament(
        name=data["name"],
        description=data["description"],
        date_time=data["date_time"],
        max_players=data.get("max_players"),
        prize=prize
    )
    
    await state.clear()
    await msg.answer(
        f"✅ Турнир <b>{data['name']}</b> создан!",
        reply_markup=kb_admin_panel,
        parse_mode="HTML"
    )

async def tournament_list(callback: CallbackQuery):
    tournaments = await get_all_tournaments()
    if not tournaments:
        await callback.message.edit_text(
            "🏆 Пока нет турниров",
            reply_markup=kb_admin_panel
        )
        await callback.answer()
        return
    
    text = "🏆 <b>Список турниров:</b>\n\n"
    for tour in tournaments:
        status_emoji = "🟢" if tour["status"] == "upcoming" else "🔴" if tour["status"] == "completed" else "🟡"
        text += f"{status_emoji} <b>{tour['name']}</b>\n"
        text += f"📅 {tour['date_time']}\n"
        if tour["max_players"]:
            text += f"👥 Макс. игроков: {tour['max_players']}\n"
        if tour["prize"]:
            text += f"🏆 Приз: {tour['prize']}\n"
        text += f"🆔 ID: {tour['id']}\n\n"
    
    await callback.message.edit_text(text, reply_markup=kb_admin_panel, parse_mode="HTML")
    await callback.answer()

# ── Welcome Message Management ───────────────────────────────────────────────────
async def welcome_edit(msg: types.Message, state: FSMContext):
    await state.update_data(welcome_message=msg.text)
    await add_welcome_message(msg.text)
    await state.clear()
    await msg.answer(
        "✅ Приветственное сообщение обновлено!",
        reply_markup=kb_admin_panel
    )

async def welcome_view(callback: CallbackQuery):
    welcome = await get_active_welcome_message()
    if welcome:
        text = f"📝 <b>Текущее приветственное сообщение:</b>\n\n{welcome['message']}"
    else:
        text = "📝 Приветственное сообщение не установлено"
    
    await callback.message.edit_text(text, reply_markup=kb_admin_panel, parse_mode="HTML")
    await callback.answer()

# ── Notification Management ─────────────────────────────────────────────────────
async def notification_create_tournament_select(callback: CallbackQuery, state: FSMContext):
    tournaments = await get_all_tournaments()
    if not tournaments:
        await callback.message.edit_text(
            "🏆 Сначала создайте турнир",
            reply_markup=kb_admin_panel
        )
        await callback.answer()
        return
    
    buttons = []
    for tour in tournaments:
        buttons.append([InlineKeyboardButton(
            text=f"{tour['name']} ({tour['date_time']})",
            callback_data=f"notif:tour:{tour['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")])
    
    await callback.message.edit_text(
        "🏆 Выбери турнир для рассылки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

async def notification_tournament_selected(callback: CallbackQuery, state: FSMContext):
    tournament_id = int(callback.data.split(":")[2])
    await state.update_data(tournament_id=tournament_id)
    await callback.answer()
    await state.set_state(Admin.waiting_notification_message)
    await callback.message.answer(
        "📝 Введи текст сообщения для рассылки:",
        reply_markup=kb_admin_panel
    )

async def notification_create_message(msg: types.Message, state: FSMContext):
    await state.update_data(notification_message=msg.text)
    await msg.answer("⏰ Введи время отправки (формат: YYYY-MM-DD HH:MM):")
    await state.set_state(Admin.waiting_notification_time)

async def notification_create_time(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    tournament_id = data["tournament_id"]
    message = data["notification_message"]
    send_time = msg.text
    
    await add_tournament_notification(tournament_id, message, send_time)
    await state.clear()
    await msg.answer(
        "✅ Рассылка запланирована!",
        reply_markup=kb_admin_panel
    )


# ── Admin Management ─────────────────────────────────────────────────────────────
async def admin_manage_id(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("admin_action", "add")
    
    print(f"DEBUG: admin_manage_id called with action: {action}, data: {data}")
    
    try:
        admin_id = int(msg.text.strip())
        
        if action == "add":
            username = msg.from_user.username or ""
            await add_admin(admin_id, username, msg.from_user.id)
            await state.clear()
            await msg.answer(
                f"✅ Пользователь <code>{admin_id}</code> добавлен в админы!",
                reply_markup=kb_admin_panel
            )
        elif action == "remove":
            # Don't allow removing self
            if admin_id == msg.from_user.id:
                await msg.answer("⚠️ Нельзя удалить самого себя из админов")
                return
            
            await remove_admin(admin_id)
            await state.clear()
            await msg.answer(
                f"✅ Пользователь <code>{admin_id}</code> удален из админов!",
                reply_markup=kb_admin_panel
            )
    except ValueError:
        await msg.answer("⚠️ Введи корректный числовой ID пользователя")
    except Exception as e:
        print(f"ERROR in admin_manage_id: {e}")
        await msg.answer("⚠️ Произошла ошибка при обработке")

async def admin_list(callback: CallbackQuery):
    try:
        # Принудительно создаем таблицу если нет
        from db import init_db
        await init_db()
        
        admins = await get_all_admins()
        if not admins:
            text = "📝 <b>Список администраторов:</b>\n\n➕ Админов пока нет"
        else:
            text = "📝 <b>Список администраторов:</b>\n\n"
            for i, admin in enumerate(admins, 1):
                username = admin['username'] or 'Без username'
                added_at = admin['added_at'][:16] if admin['added_at'] else 'Неизвестно'
                text += f"{i}. @{username} (<code>{admin['tg_id']}</code>)\n   📅 Добавлен: {added_at}\n\n"
        
        try:
            await callback.message.edit_text(text, reply_markup=kb_admin_menu, parse_mode="HTML")
        except Exception as e:
            print(f"Error editing message: {e}")
            # Если редактирование не удалось, отправляем новое сообщение
            await callback.message.answer(text, reply_markup=kb_admin_menu, parse_mode="HTML")
            
    except Exception as e:
        print(f"Error in admin_list: {e}")
        try:
            await callback.message.edit_text("⚠️ Ошибка при загрузке списка админов", reply_markup=kb_admin_menu)
        except:
            await callback.message.answer("⚠️ Ошибка при загрузке списка админов", reply_markup=kb_admin_menu)
    
    await callback.answer()


# ── Channel Settings Management ───────────────────────────────────────────────────
async def channel_edit_link(msg: types.Message, state: FSMContext):
    await update_channel_settings(channel_link=msg.text.strip())
    await state.clear()
    await msg.answer(
        "✅ Ссылка на каналы обновлена!",
        reply_markup=kb_admin_panel
    )

async def channel_edit_discord(msg: types.Message, state: FSMContext):
    await update_channel_settings(discord_link=msg.text.strip())
    await state.clear()
    await msg.answer(
        "✅ Discord ссылка обновлена!",
        reply_markup=kb_admin_panel
    )

async def channel_view(callback: CallbackQuery):
    settings = await get_channel_settings()
    
    status = "✅ Включено" if settings.get("require_subscription") else "❌ Выключено"
    text = (
        f"📢 <b>Настройки канала:</b>\n\n"
        f"🔗 Ссылка на канал: {settings.get('channel_link', 'Не установлена')}\n"
        f"🎮 Discord ссылка: {settings.get('discord_link', 'Не установлена')}\n"
        f"🔔 Требовать подписку: {status}"
    )
    
    await callback.message.edit_text(text, reply_markup=kb_channel_menu, parse_mode="HTML")
    await callback.answer()

async def channel_toggle_subscription(callback: CallbackQuery):
    settings = await get_channel_settings()
    new_status = not settings.get("require_subscription", False)
    
    await update_channel_settings(require_subscription=new_status)
    
    status_text = "включено" if new_status else "выключено"
    text = f"🔔 Требование подписки {status_text}"
    
    try:
        await callback.message.edit_text(text, reply_markup=kb_channel_menu)
    except Exception as e:
        print(f"Error editing message: {e}")
        # Если редактирование не удалось, отправляем новое сообщение
        await callback.message.answer(text, reply_markup=kb_channel_menu)
    
    await callback.answer()


# ── Contact Admins ───────────────────────────────────────────────────────────────
async def contact_admins_handler(msg: types.Message, state: FSMContext):
    """Обработка кнопки 'Обратиться к админам'"""
    await msg.answer(
        "💬 <b>Напишите ваше сообщение администраторам:</b>\n\n"
        "Отправьте сообщение и оно будет доставлено всем админам.",
        parse_mode="HTML"
    )
    await state.set_state(ContactAdmin.waiting_message)


async def contact_admins_message_handler(msg: types.Message, bot: Bot):
    """Обработка сообщения для админов"""
    try:
        admins = await get_all_admins()
        admin_ids = list(ADMIN_IDS) + [admin['tg_id'] for admin in admins]
        
        # Удаляем дубликаты
        admin_ids = list(set(admin_ids))
        
        if not admin_ids:
            await msg.answer("⚠️ В данный момент нет доступных администраторов")
            return
        
        # Отправляем сообщение всем админам
        success_count = 0
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"💬 <b>Сообщение от пользователя:</b>\n\n"
                         f"👤 @{msg.from_user.username or 'Нет username'} (<code>{msg.from_user.id}</code>)\n"
                         f"💭 {msg.text}",
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
        
        await msg.answer(
            f"✅ Ваше сообщение отправлено {success_count} администраторам!",
            reply_markup=_main_kb(msg.from_user.id)
        )
    except Exception as e:
        print(f"Error in contact_admins_message_handler: {e}")
        await msg.answer("⚠️ Произошла ошибка при отправке сообщения")


# ── Discord Handler ───────────────────────────────────────────────────────────────
async def discord_handler(msg: types.Message, bot: Bot):
    # Get Discord link from channel settings or use default
    settings = await get_channel_settings()
    discord_link = settings.get("discord_link", "https://discord.gg/your-server")
    
    await msg.answer(
        f"🎮 <b>Наш Discord сервер:</b>\n\n"
        f"🔗 {discord_link}\n\n"
        f"Присоединяйтесь к сообществу!",
        reply_markup=_main_kb(msg.from_user.id),
        parse_mode="HTML"
    )


# ── SuperUser Handlers ───────────────────────────────────────────────────────────────
from states import SuperUser

async def superuser_command(msg: types.Message, state: FSMContext):
    """Команда /superuser - вход в секретное меню"""
    await msg.answer("🔐 Введите пароль для доступа к секретному меню:")
    await state.set_state(SuperUser.waiting_password)


async def superuser_password_handler(msg: types.Message, state: FSMContext):
    """Обработка ввода пароля superuser"""
    correct_password = await get_superuser_password()
    
    if msg.text.strip() == correct_password:
        await state.clear()
        await log_activity(msg.from_user.id, msg.from_user.username, "SUPERUSER_LOGIN", "Успешный вход")
        await msg.answer(
            "🔓 <b>Добро пожаловать в секретное меню!</b>\n\n"
            "Здесь вы можете:\n"
            "• Просматривать логи активности\n"
            "• Просматривать логи бота\n"
            "• Управлять пользователями\n"
            "• Менять пароль\n"
            "• Очищать логи",
            reply_markup=kb_superuser_main,
            parse_mode="HTML"
        )
    else:
        await log_activity(msg.from_user.id, msg.from_user.username, "SUPERUSER_FAIL", "Неверный пароль")
        await msg.answer("❌ Неверный пароль!")
        await state.clear()


async def superuser_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка callback'ов superuser меню"""
    action = callback.data.split(":")[1]
    
    if action == "back":
        await callback.message.edit_text(
            "🔓 <b>Секретное меню</b>",
            reply_markup=kb_superuser_main,
            parse_mode="HTML"
        )
        await callback.answer()
    
    elif action == "exit":
        await callback.message.edit_text("🔒 Секретное меню закрыто")
        await callback.answer()
        await state.clear()
    
    elif action == "activity_logs":
        logs = await get_activity_logs(20)
        if not logs:
            text = "📊 <b>Логи активности:</b>\n\nЛоги пусты"
        else:
            text = "📊 <b>Логи активности (последние 20):</b>\n\n"
            for log in logs:
                text += f"👤 {log['username']} (<code>{log['user_id']}</code>)\n"
                text += f"   Действие: {log['action']}\n"
                if log['details']:
                    text += f"   Детали: {log['details']}\n"
                text += f"   ⏰ {log['created_at']}\n\n"
        
        try:
            await callback.message.edit_text(text, reply_markup=kb_superuser_back, parse_mode="HTML")
        except:
            await callback.message.answer(text, reply_markup=kb_superuser_back, parse_mode="HTML")
        await callback.answer()
    
    elif action == "bot_logs":
        logs = await get_bot_logs(20)
        if not logs:
            text = "📝 <b>Логи бота:</b>\n\nЛоги пусты"
        else:
            text = "📝 <b>Логи бота (последние 20):</b>\n\n"
            for log in logs:
                emoji = "ℹ️" if log['level'] == 'INFO' else "⚠️" if log['level'] == 'WARNING' else "❌"
                text += f"{emoji} [{log['level']}] {log['message']}\n"
                text += f"   ⏰ {log['created_at']}\n\n"
        
        try:
            await callback.message.edit_text(text, reply_markup=kb_superuser_back, parse_mode="HTML")
        except:
            await callback.message.answer(text, reply_markup=kb_superuser_back, parse_mode="HTML")
        await callback.answer()
    
    elif action == "all_users":
        users = await get_all_users()
        if not users:
            text = "👥 <b>Пользователи:</b>\n\nНет зарегистрированных пользователей"
        else:
            text = f"👥 <b>Все пользователи ({len(users)}):</b>\n\n"
            for i, user in enumerate(users, 1):
                text += f"{i}. @{user.get('username', 'Нет')} (<code>{user['tg_id']}</code>)\n"
                text += f"   Epic: {user['epic']} | Discord: {user['discord']}\n"
                text += f"   MMR: {user['rank']} | Пик: {user['peak_rank']}\n\n"
        
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            try:
                await callback.message.edit_text(chunk, reply_markup=kb_superuser_back, parse_mode="HTML")
            except:
                await callback.message.answer(chunk, reply_markup=kb_superuser_back, parse_mode="HTML")
                break
        await callback.answer()
    
    elif action == "change_password":
        await callback.message.edit_text("🔑 Введите новый пароль:")
        await state.set_state(SuperUser.waiting_new_password)
        await callback.answer()
    
    elif action == "clear_logs":
        await callback.message.edit_text(
            "🧹 <b>Очистить все логи?</b>\nЭто действие необратимо!",
            reply_markup=kb_clear_logs_confirm,
            parse_mode="HTML"
        )
        await callback.answer()
    
    elif action == "clear_confirm":
        await clear_activity_logs()
        await clear_bot_logs()
        await log_activity(callback.from_user.id, callback.from_user.username, "CLEAR_LOGS", "Все логи очищены")
        await callback.message.edit_text(
            "✅ <b>Все логи очищены!</b>",
            reply_markup=kb_superuser_main,
            parse_mode="HTML"
        )
        await callback.answer("Логи очищены")
    
    elif action == "stats":
        user_count = await count_users()
        admins = await get_all_admins()
        
        text = (
            f"📈 <b>Общая статистика:</b>\n\n"
            f"👥 Пользователей: <b>{user_count}</b>\n"
            f"👑 Администраторов: <b>{len(admins)}</b>"
        )
        
        await callback.message.edit_text(text, reply_markup=kb_superuser_back, parse_mode="HTML")
        await callback.answer()
    
    elif action == "backup":
        await callback.message.edit_text("💾 <b>Создание бэкапа...</b>")
        await callback.answer()
        
        backup_json = await create_backup()
        if backup_json:
            counts = await get_backup_count()
            # Send backup as a file
            from io import BytesIO
            backup_bytes = BytesIO(backup_json.encode('utf-8'))
            backup_bytes.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            await callback.message.answer_document(
                document=backup_bytes,
                caption=f"💾 <b>Бэкап создан!</b>\n\n"
                        f"👥 Пользователей: {counts['users']}\n"
                        f"👑 Админов: {counts['admins']}\n"
                        f"🏆 Турниров: {counts['tournaments']}",
                parse_mode="HTML"
            )
            await callback.message.delete()
        else:
            await callback.message.edit_text("❌ Ошибка при создании бэкапа!", reply_markup=kb_superuser_back)
    
    elif action == "restore":
        await callback.message.edit_text(
            "📂 <b>Восстановление из бэкапа</b>\n\n"
            "Отправьте JSON файл бэкапа для восстановления.\n"
            "⚠️ <b>Внимание!</b> Это удалит все текущие данные и заменит их данными из бэкапа.",
            reply_markup=kb_superuser_back,
            parse_mode="HTML"
        )
        await callback.answer()


async def superuser_new_password_handler(msg: types.Message, state: FSMContext):
    """Обработка нового пароля superuser"""
    new_password = msg.text.strip()
    
    if len(new_password) < 4:
        await msg.answer("⚠️ Пароль должен быть не менее 4 символов. Введите новый пароль:")
        return
    
    await set_superuser_password(new_password)
    await log_activity(msg.from_user.id, msg.from_user.username, "PASSWORD_CHANGE", "Пароль изменён")
    await state.clear()
    await msg.answer(
        "✅ <b>Пароль успешно изменён!</b>",
        reply_markup=kb_superuser_main,
        parse_mode="HTML"
    )


async def superuser_restore_handler(msg: types.Message, state: FSMContext):
    """Обработка восстановления из бэкапа (файл)"""
    if not msg.document:
        await msg.answer("⚠️ Пожалуйста, отправьте JSON файл бэкапа.")
        return
    
    try:
        # Download the file
        file = await bot.get_file(msg.document.file_id)
        file_content = await bot.download_file(file.file_path)
        backup_json = file_content.decode('utf-8')
        
        # Confirm restore
        await msg.answer("⏳ <b>Восстановление из бэкапа...</b>", parse_mode="HTML")
        
        success = await restore_from_backup(backup_json)
        
        if success:
            await log_activity(msg.from_user.id, msg.from_user.username, "RESTORE", "Восстановление из бэкапа выполнено")
            await msg.answer(
                "✅ <b>Данные успешно восстановлены из бэкапа!</b>",
                reply_markup=kb_superuser_main,
                parse_mode="HTML"
            )
        else:
            await msg.answer(
                "❌ <b>Ошибка при восстановлении!</b>\nПроверьте формат файла.",
                reply_markup=kb_superuser_back,
                parse_mode="HTML"
            )
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")
        await log_bot("ERROR", f"Ошибка восстановления: {e}")
