from aiogram.fsm.state import State, StatesGroup


class MyData(StatesGroup):
    waiting_epic = State()
    waiting_discord = State()
    waiting_rank = State()
    waiting_peak_rank = State()
    waiting_tracker = State()

class Registration(StatesGroup):
    waiting_tournament_select = State()
    epic_id = State()
    discord = State()
    rank = State()
    peak_rank = State()
    rank_mmr = State()
    peak_rank_mmr = State()
    tracker = State()


class Admin(StatesGroup):
    waiting_kick_id = State()
    waiting_tournament_name = State()
    waiting_tournament_description = State()
    waiting_tournament_date = State()
    waiting_tournament_players = State()
    waiting_tournament_prize = State()
    waiting_welcome_message = State()
    waiting_notification_message = State()
    waiting_notification_time = State()
    waiting_tournament_select = State()
    waiting_admin_id = State()
    waiting_channel_link = State()
    waiting_discord_link = State()
    waiting_broadcast_message = State()
    waiting_post_reg_message = State()
    waiting_search_query = State()
    waiting_user_reply = State()  # Для ответа пользователю


class ContactAdmin(StatesGroup):
    waiting_message = State()


class SuperUser(StatesGroup):
    waiting_password = State()
    waiting_new_password = State()
