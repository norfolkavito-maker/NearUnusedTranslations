from aiogram import types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery

from db import check_user, add_user, get_all_users, get_user, delete_user
from states import Registration
from keyboards import (
    kb_main, kb_tiers, kb_subtiers, kb_divisions,
    TIERS, get_rank_label, get_auto_mmr
)
from config import CHANNEL_ID, ADMIN_ID


async def start_handler(msg: types.Message):
    await msg.answer("Привет! Жми Регистрация чтобы участвовать.", reply_markup=kb_main)


async def registration_handler(msg: types.Message, state: FSMContext, bot: Bot):
    tg_id = msg.from_user.id
    if await check_user(tg_id):
        await msg.answer("Ты уже зарегистрирован.")
        return

    try:
        member = await bot.get_chat_member(CHANNEL_ID, tg_id)
        if member.status in ["left", "kicked"]:
            await msg.answer(f"Подпишись на {CHANNEL_ID} чтобы зарегистрироваться!")
            return
    except Exception:
        pass

    await msg.answer("Введите ваш Epic ID:")
    await state.set_state(Registration.epic_id)


async def process_epic_id(msg: types.Message, state: FSMContext):
    await state.update_data(epic=msg.text)
    await msg.answer("Введите ваш Discord (например User#1234):")
    await state.set_state(Registration.discord)


async def process_discord(msg: types.Message, state: FSMContext):
    await state.update_data(discord=msg.text)
    await msg.answer(
        "Выберите ваш <b>текущий ранг</b> (MMR указан приблизительно для 2v2):",
        reply_markup=kb_tiers("r"),
        parse_mode="HTML"
    )
    await state.set_state(Registration.rank)


# ── Tier selected ────────────────────────────────────────────────────────────
async def on_tier(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str = callback.data.split(":")
    tier_idx = int(tier_idx_str)
    tier_name = TIERS[tier_idx][1]
    label = "текущий" if prefix == "r" else "пиковый"

    if tier_name == "SSL":
        await callback.message.edit_text(
            f"⚡ <b>SSL</b> — введи свой <b>{label} MMR</b> (2600+):",
            parse_mode="HTML"
        )
        if prefix == "r":
            await state.set_state(Registration.rank_mmr)
        else:
            await state.set_state(Registration.peak_rank_mmr)
    else:
        await callback.message.edit_text(
            f"Выберите <b>{tier_name}</b> 1, 2 или 3:",
            reply_markup=kb_subtiers(prefix, tier_idx),
            parse_mode="HTML"
        )
    await callback.answer()


# ── Subtier selected ─────────────────────────────────────────────────────────
async def on_subtier(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str, sub_str = callback.data.split(":")
    tier_idx, sub = int(tier_idx_str), int(sub_str)
    tier_name = TIERS[tier_idx][1]

    await callback.message.edit_text(
        f"Выберите дивизион для <b>{tier_name} {sub}</b>:",
        reply_markup=kb_divisions(prefix, tier_idx, sub),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Division selected (final step for rank) ──────────────────────────────────
async def on_division(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str, sub_str, div_str = callback.data.split(":")
    tier_idx, sub, div = int(tier_idx_str), int(sub_str), int(div_str)

    rank_label = get_rank_label(tier_idx, sub, div)
    mmr = get_auto_mmr(tier_idx, sub, div)
    rank_value = f"{rank_label} (~{mmr} MMR)"

    if prefix == "r":
        await state.update_data(rank=rank_value)
        await callback.message.edit_text(
            f"✅ Текущий ранг: <b>{rank_label}</b> (~{mmr} MMR)\n\n"
            f"Теперь выберите ваш <b>пиковый ранг</b>:",
            reply_markup=kb_tiers("p"),
            parse_mode="HTML"
        )
        await state.set_state(Registration.peak_rank)
    else:
        await _save_and_finish(callback, state, peak_rank=rank_value)
    await callback.answer()


# ── Manual MMR requested ─────────────────────────────────────────────────────
async def on_manual_mmr(callback: CallbackQuery, state: FSMContext):
    _, prefix = callback.data.split(":")
    label = "текущий" if prefix == "r" else "пиковый"
    await callback.message.edit_text(
        f"✏️ Введи свой <b>{label} MMR</b> числом (например: 1450):",
        parse_mode="HTML"
    )
    if prefix == "r":
        await state.set_state(Registration.rank_mmr)
    else:
        await state.set_state(Registration.peak_rank_mmr)
    await callback.answer()


# ── Back buttons ─────────────────────────────────────────────────────────────
async def on_back_to_tiers(callback: CallbackQuery, state: FSMContext):
    _, prefix = callback.data.split(":")
    label = "текущий" if prefix == "r" else "пиковый"
    await callback.message.edit_text(
        f"Выберите ваш <b>{label} ранг</b>:",
        reply_markup=kb_tiers(prefix),
        parse_mode="HTML"
    )
    await callback.answer()


async def on_back_to_subtiers(callback: CallbackQuery, state: FSMContext):
    _, prefix, tier_idx_str = callback.data.split(":")
    tier_idx = int(tier_idx_str)
    tier_name = TIERS[tier_idx][1]
    await callback.message.edit_text(
        f"Выберите <b>{tier_name}</b> 1, 2 или 3:",
        reply_markup=kb_subtiers(prefix, tier_idx),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Text MMR input ───────────────────────────────────────────────────────────
async def process_rank_mmr_text(msg: types.Message, state: FSMContext):
    try:
        mmr = int(msg.text.strip())
        if mmr < 0 or mmr > 10000:
            raise ValueError
    except ValueError:
        await msg.answer("Введи корректное число MMR, например: 1450")
        return

    rank_value = f"MMR: {mmr}"
    await state.update_data(rank=rank_value)
    await msg.answer(
        f"✅ Текущий MMR: <b>{mmr}</b>\n\nТеперь выберите ваш <b>пиковый ранг</b>:",
        reply_markup=kb_tiers("p"),
        parse_mode="HTML"
    )
    await state.set_state(Registration.peak_rank)


async def process_peak_rank_mmr_text(msg: types.Message, state: FSMContext):
    try:
        mmr = int(msg.text.strip())
        if mmr < 0 or mmr > 10000:
            raise ValueError
    except ValueError:
        await msg.answer("Введи корректное число MMR, например: 2700")
        return

    await _save_and_finish_msg(msg, state, peak_rank=f"MMR: {mmr}")


# ── Helpers ──────────────────────────────────────────────────────────────────
async def _save_and_finish(callback: CallbackQuery, state: FSMContext, peak_rank: str):
    data = await state.get_data()
    tg_id = callback.from_user.id
    username = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    await add_user(
        tg_id=tg_id, username=username,
        epic=data.get("epic", ""), discord=data.get("discord", ""),
        rank=data.get("rank", ""), peak_rank=peak_rank
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ Пиковый ранг: <b>{peak_rank}</b>\n\n🎉 Ты успешно зарегистрирован! Ожидай начала турнира.",
        parse_mode="HTML"
    )


async def _save_and_finish_msg(msg: types.Message, state: FSMContext, peak_rank: str):
    data = await state.get_data()
    tg_id = msg.from_user.id
    username = f"@{msg.from_user.username}" if msg.from_user.username else msg.from_user.full_name
    await add_user(
        tg_id=tg_id, username=username,
        epic=data.get("epic", ""), discord=data.get("discord", ""),
        rank=data.get("rank", ""), peak_rank=peak_rank
    )
    await state.clear()
    await msg.answer(
        f"✅ Пиковый MMR: <b>{peak_rank}</b>\n\n🎉 Ты успешно зарегистрирован! Ожидай начала турнира.",
        parse_mode="HTML"
    )


# ── Admin commands ───────────────────────────────────────────────────────────
async def me_handler(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user:
        await msg.answer("Ты не зарегистрирован. Нажми кнопку Регистрация.")
        return
    await msg.answer(
        f"📋 <b>Твои данные:</b>\n"
        f"Telegram: {user.get('username', '—')}\n"
        f"Epic ID: {user['epic']}\n"
        f"Discord: {user['discord']}\n"
        f"Ранг: {user['rank']}\n"
        f"Пик ранг: {user['peak_rank']}",
        parse_mode="HTML"
    )


async def list_handler(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Нет доступа.")
        return

    users = await get_all_users()
    if not users:
        await msg.answer("Никто ещё не зарегистрировался.")
        return

    text = f"👥 <b>Зарегистрировано: {len(users)}</b>\n\n"
    for i, u in enumerate(users, 1):
        text += (
            f"{i}. {u.get('username', '—')} | <code>{u['tg_id']}</code>\n"
            f"   Epic: {u['epic']} | Discord: {u['discord']}\n"
            f"   Ранг: {u['rank']} | Пик: {u['peak_rank']}\n\n"
        )

    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await msg.answer(chunk, parse_mode="HTML")


async def kick_handler(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Нет доступа.")
        return

    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /kick <tg_id>")
        return

    try:
        tg_id = int(args[1])
    except ValueError:
        await msg.answer("Неверный ID.")
        return

    if not await check_user(tg_id):
        await msg.answer("Пользователь не найден.")
        return

    await delete_user(tg_id)
    await msg.answer(f"Пользователь {tg_id} удалён из регистрации.")
