from aiogram import types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from db import check_user, add_user
from states import Registration
from keyboards import kb_main
from config import CHANNEL_ID


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
