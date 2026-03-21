from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    epic_id = State()
    discord = State()
    rank = State()
    peak_rank = State()
