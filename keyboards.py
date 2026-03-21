from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

kb_main = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Регистрация")]],
    resize_keyboard=True
)

RANKS = [
    ("🥉 Bronze I",    "Bronze I",    "0–999"),
    ("🥉 Bronze II",   "Bronze II",   "1000–1999"),
    ("🥉 Bronze III",  "Bronze III",  "2000–2999"),
    ("🥈 Silver I",    "Silver I",    "3000–3999"),
    ("🥈 Silver II",   "Silver II",   "4000–4999"),
    ("🥈 Silver III",  "Silver III",  "5000–5999"),
    ("🥇 Gold I",      "Gold I",      "6000–6999"),
    ("🥇 Gold II",     "Gold II",     "7000–7999"),
    ("🥇 Gold III",    "Gold III",    "8000–8999"),
    ("💎 Platinum I",  "Platinum I",  "9000–9999"),
    ("💎 Platinum II", "Platinum II", "10000–10999"),
    ("💎 Platinum III","Platinum III","11000–11999"),
    ("💠 Diamond I",   "Diamond I",   "12000–12999"),
    ("💠 Diamond II",  "Diamond II",  "13000–13999"),
    ("💠 Diamond III", "Diamond III", "14000–14999"),
    ("⚡ Elite",       "Elite",       "15000–17499"),
    ("🏆 Champion",    "Champion",    "17500–19999"),
    ("👑 Unreal",      "Unreal",      "20000+"),
]


def rank_keyboard(prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for label, value, mmr in RANKS:
        buttons.append([InlineKeyboardButton(
            text=f"{label}  •  MMR: {mmr}",
            callback_data=f"{prefix}:{value}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


kb_rank = rank_keyboard("rank")
kb_peak_rank = rank_keyboard("peak")
