from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

kb_main = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🎮 Регистрация"), KeyboardButton(text="📋 Мои данные")]],
    resize_keyboard=True
)

kb_admin_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎮 Регистрация"), KeyboardButton(text="📋 Мои данные")],
        [KeyboardButton(text="⚙️ Админ-панель")],
    ],
    resize_keyboard=True
)

TIERS = [
    ("🟫 Бронза",        "Бронза",         "0–305"),
    ("⬜ Серебро",        "Серебро",        "319–485"),
    ("🟨 Золото",         "Золото",         "501–676"),
    ("🟦 Платина",        "Платина",        "693–876"),
    ("💎 Даймонд",       "Даймонд",        "894–1089"),
    ("🏆 Чемпион",        "Чемпион",        "1108–1326"),
    ("👑 Гранд-Чемпион", "Гранд-Чемпион",  "1435–1778"),
    ("⚡ SSL",            "SSL",            "1860+"),
]

# Exact MMR values per (tier_idx, subtier, division) for 2v2 Doubles
RANK_MMR_TABLE = {
    (0,1,1): 0,    (0,1,2): 161,  (0,1,3): 175,  (0,1,4): 189,
    (0,2,1): 204,  (0,2,2): 218,  (0,2,3): 232,  (0,2,4): 247,
    (0,3,1): 261,  (0,3,2): 275,  (0,3,3): 290,  (0,3,4): 305,

    (1,1,1): 319,  (1,1,2): 334,  (1,1,3): 349,  (1,1,4): 364,
    (1,2,1): 379,  (1,2,2): 394,  (1,2,3): 409,  (1,2,4): 424,
    (1,3,1): 439,  (1,3,2): 454,  (1,3,3): 469,  (1,3,4): 485,

    (2,1,1): 501,  (2,1,2): 516,  (2,1,3): 532,  (2,1,4): 548,
    (2,2,1): 564,  (2,2,2): 580,  (2,2,3): 596,  (2,2,4): 612,
    (2,3,1): 628,  (2,3,2): 644,  (2,3,3): 660,  (2,3,4): 676,

    (3,1,1): 693,  (3,1,2): 709,  (3,1,3): 726,  (3,1,4): 742,
    (3,2,1): 759,  (3,2,2): 775,  (3,2,3): 792,  (3,2,4): 809,
    (3,3,1): 826,  (3,3,2): 842,  (3,3,3): 859,  (3,3,4): 876,

    (4,1,1): 894,  (4,1,2): 911,  (4,1,3): 928,  (4,1,4): 946,
    (4,2,1): 964,  (4,2,2): 981,  (4,2,3): 999,  (4,2,4): 1017,
    (4,3,1): 1035, (4,3,2): 1053, (4,3,3): 1071, (4,3,4): 1089,

    (5,1,1): 1108, (5,1,2): 1126, (5,1,3): 1145, (5,1,4): 1164,
    (5,2,1): 1184, (5,2,2): 1203, (5,2,3): 1223, (5,2,4): 1243,
    (5,3,1): 1264, (5,3,2): 1284, (5,3,3): 1305, (5,3,4): 1326,

    (6,1,1): 1435, (6,1,2): 1450, (6,1,3): 1471, (6,1,4): 1493,
    (6,2,1): 1575, (6,2,2): 1595, (6,2,3): 1616, (6,2,4): 1637,
    (6,3,1): 1715, (6,3,2): 1736, (6,3,3): 1757, (6,3,4): 1778,
}


def get_rank_label(tier_idx: int, sub: int, div: int) -> str:
    return f"{TIERS[tier_idx][1]} {sub} / Дивизион {div}"


def get_auto_mmr(tier_idx: int, sub: int, div: int) -> int:
    return RANK_MMR_TABLE.get((tier_idx, sub, div), 0)


def kb_sub_check(channel_link: str, group_link: str = "") -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="📢 Подписаться на канал", url=channel_link)]]
    if group_link:
        buttons.append([InlineKeyboardButton(text="👥 Вступить в группу", url=group_link)])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался — проверить", callback_data="sub_check")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


kb_admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋 Список участников", callback_data="adm:list")],
    [InlineKeyboardButton(text="📊 Статистика",        callback_data="adm:stats")],
    [
        InlineKeyboardButton(text="🗑 Удалить игрока", callback_data="adm:kick"),
        InlineKeyboardButton(text="💥 Удалить всех",   callback_data="adm:deleteall"),
    ],
])

kb_deleteall_confirm = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Да, удалить всех", callback_data="adm:deleteall_yes"),
    InlineKeyboardButton(text="❌ Отмена",            callback_data="adm:cancel"),
]])


def kb_tiers(prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for i, (label, name, mmr_range) in enumerate(TIERS):
        buttons.append([InlineKeyboardButton(
            text=f"{label}  •  {mmr_range} MMR",
            callback_data=f"rt:{prefix}:{i}"
        )])
    buttons.append([InlineKeyboardButton(
        text="✏️ Ввести MMR вручную",
        callback_data=f"rm:{prefix}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_subtiers(prefix: str, tier_idx: int) -> InlineKeyboardMarkup:
    name = TIERS[tier_idx][1]
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{name} 1", callback_data=f"rs:{prefix}:{tier_idx}:1"),
            InlineKeyboardButton(text=f"{name} 2", callback_data=f"rs:{prefix}:{tier_idx}:2"),
            InlineKeyboardButton(text=f"{name} 3", callback_data=f"rs:{prefix}:{tier_idx}:3"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"rb:{prefix}")],
    ])


def kb_divisions(prefix: str, tier_idx: int, sub: int) -> InlineKeyboardMarkup:
    buttons = []
    for d in range(1, 5):
        mmr = RANK_MMR_TABLE.get((tier_idx, sub, d), "?")
        buttons.append([InlineKeyboardButton(
            text=f"Дивизион {d}  •  {mmr} MMR",
            callback_data=f"rd:{prefix}:{tier_idx}:{sub}:{d}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"rsb:{prefix}:{tier_idx}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
