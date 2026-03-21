from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    epic_id = State()
    discord = State()
    rank = State()
    rank_mmr = State()
    peak_rank = State()
    peak_rank_mmr = State()
    tracker = State()


class Admin(StatesGroup):
    waiting_kick_id = State()
