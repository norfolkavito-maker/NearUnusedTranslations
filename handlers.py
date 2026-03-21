from aiogram import types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery

from db import check_user, add_user, get_all_users, get_user, delete_user, delete_all_users, count_users
from states import Registration, Admin
from keyboards import (
    kb_main, kb_admin_main, kb_tiers, kb_subtiers, kb_divisions,
    kb_sub_check, kb_admin_panel, kb_deleteall_confirm,
    TIERS, get_rank_label, get_auto_mmr,
)
from config import CHANNEL_ID, CHANNEL_LINK, GROUP_LINK, ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _main_kb(user_id: int):
    return kb_admin_main if is_admin(user_id) else kb_main


# ── /start ───────────────────────────────────────────────────────────────────
async def start_handler(msg: types.Message):
    await msg.answer(
        "👋 Привет! Нажми <b>🎮 Регистрация</b> чтобы участвовать в турнире.\n"
        "Команда <b>📋 Мои данные</b> покажет твою анкету.",
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
        await callback.answer()
        return

    try:
        member = await bot.get_chat_member(CHANNEL_ID, tg_id)
        subscribed = member.status not in ["left", "kicked"]
    except Exception:
        subscribed = True

    if not subscribed:
        await callback.answer("❌ Ты ещё не подписался!", show_alert=True)
        return

    await callback.message.edit_text("✅ Подписка подтверждена!")
    await _start_registration(callback.message)
    await state.set_state(Registration.epic_id)
    await callback.answer()


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
    step = "3️⃣" if prefix == "r" else "4️⃣"
    label = "актуальный" if prefix == "r" else "пиковый"

    if tier_name == "SSL":
        await callback.message.edit_text(
            f"⚡ <b>SSL</b> — введи свой <b>{label} MMR</b> (от 1860):",
            parse_mode="HTML"
        )
        await state.set_state(Registration.rank_mmr if prefix == "r" else Registration.peak_rank_mmr)
    else:
        await callback.message.edit_text(
            f"{step} Выбери <b>{tier_name}</b> 1, 2 или 3:",
            reply_markup=kb_subtiers(prefix, tier_idx),
            parse_mode="HTML"
        )
    await callback.answer()


async def on_subtier(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str, sub_str = callback.data.split(":")
    tier_idx, sub = int(tier_idx_str), int(sub_str)
    step = "3️⃣" if prefix == "r" else "4️⃣"
    await callback.message.edit_text(
        f"{step} Выбери дивизион для <b>{TIERS[tier_idx][1]} {sub}</b>:",
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
            f"4️⃣ Теперь выбери свой <b>пиковый MMR</b>:",
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
