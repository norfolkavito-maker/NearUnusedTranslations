from aiogram import types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from db import check_user, add_user, get_all_users, get_user, delete_user
from states import Registration
from keyboards import kb_main
from config import CHANNEL_ID, ADMIN_ID, MAX_PLAYERS


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
            await msg.answer(f"Ты должен подписаться на канал {CHANNEL_ID} прежде чем регистрироваться!")
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
    await msg.answer("Введите ваш текущий ранг:")
    await state.set_state(Registration.rank)


async def process_rank(msg: types.Message, state: FSMContext):
    await state.update_data(rank=msg.text)
    await msg.answer("Введите ваш пик ранг:")
    await state.set_state(Registration.peak_rank)


async def process_peak_rank(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    tg_id = msg.from_user.id
    await add_user(
        tg_id=tg_id,
        epic=data.get("epic", ""),
        discord=data.get("discord", ""),
        rank=data.get("rank", ""),
        peak_rank=msg.text
    )
    await state.clear()
    await msg.answer("Ты успешно зарегистрирован! Ожидай начала турнира.")


async def list_handler(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Нет доступа.")
        return

    users = await get_all_users()
    if not users:
        await msg.answer("Никто ещё не зарегистрировался.")
        return

    text = f"👥 Зарегистрировано: {len(users)} / {MAX_PLAYERS}\n\n"
    for i, u in enumerate(users, 1):
        text += (
            f"{i}. TG: <code>{u['tg_id']}</code>\n"
            f"   Epic: {u['epic']}\n"
            f"   Discord: {u['discord']}\n"
            f"   Ранг: {u['rank']} | Пик: {u['peak_rank']}\n\n"
        )

    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await msg.answer(chunk, parse_mode="HTML")


async def me_handler(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user:
        await msg.answer("Ты не зарегистрирован. Нажми кнопку Регистрация.")
        return

    await msg.answer(
        f"📋 Твои данные:\n"
        f"Epic ID: {user['epic']}\n"
        f"Discord: {user['discord']}\n"
        f"Ранг: {user['rank']}\n"
        f"Пик ранг: {user['peak_rank']}",
        parse_mode="HTML"
    )


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
