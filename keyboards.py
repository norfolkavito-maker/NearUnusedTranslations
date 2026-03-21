from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

kb_main = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Регистрация")]],
    resize_keyboard=True
)

TIERS = [
    ("🟫 Бронза",        "Бронза",         "0–440"),
    ("⬜ Серебро",        "Серебро",        "440–725"),
    ("🟨 Золото",         "Золото",         "725–990"),
    ("🟦 Платина",        "Платина",        "990–1255"),
    ("💎 Даймонд",       "Даймонд",        "1255–1565"),
    ("🏆 Чемпион",        "Чемпион",        "1565–2020"),
    ("👑 Гранд-Чемпион", "Гранд-Чемпион",  "2020–2600"),
    ("⚡ SSL",            "SSL",            "2600+"),
]

# Approximate MMR midpoint per (tier_idx, subtier, division) for 2v2 Doubles
RANK_MMR_TABLE = {
    (0,1,1): 22,   (0,1,2): 66,   (0,1,3): 110,  (0,1,4): 154,
    (0,2,1): 193,  (0,2,2): 228,  (0,2,3): 263,  (0,2,4): 297,
    (0,3,1): 330,  (0,3,2): 361,  (0,3,3): 392,  (0,3,4): 423,

    (1,1,1): 452,  (1,1,2): 476,  (1,1,3): 501,  (1,1,4): 525,
    (1,2,1): 549,  (1,2,2): 572,  (1,2,3): 596,  (1,2,4): 619,
    (1,3,1): 643,  (1,3,2): 666,  (1,3,3): 690,  (1,3,4): 714,

    (2,1,1): 736,  (2,1,2): 758,  (2,1,3): 780,  (2,1,4): 802,
    (2,2,1): 824,  (2,2,2): 846,  (2,2,3): 868,  (2,2,4): 890,
    (2,3,1): 912,  (2,3,2): 934,  (2,3,3): 956,  (2,3,4): 978,

    (3,1,1): 998,  (3,1,2): 1015, (3,1,3): 1031, (3,1,4): 1048,
    (3,2,1): 1064, (3,2,2): 1081, (3,2,3): 1097, (3,2,4): 1114,
    (3,3,1): 1139, (3,3,2): 1172, (3,3,3): 1205, (3,3,4): 1238,

    (4,1,1): 1268, (4,1,2): 1294, (4,1,3): 1321, (4,1,4): 1347,
    (4,2,1): 1373, (4,2,2): 1398, (4,2,3): 1424, (4,2,4): 1449,
    (4,3,1): 1474, (4,3,2): 1500, (4,3,3): 1526, (4,3,4): 1552,

    (5,1,1): 1581, (5,1,2): 1614, (5,1,3): 1646, (5,1,4): 1679,
    (5,2,1): 1713, (5,2,2): 1749, (5,2,3): 1786, (5,2,4): 1822,
    (5,3,1): 1862, (5,3,2): 1908, (5,3,3): 1953, (5,3,4): 1998,

    (6,1,1): 2044, (6,1,2): 2092, (6,1,3): 2141, (6,1,4): 2189,
    (6,2,1): 2237, (6,2,2): 2285, (6,2,3): 2334, (6,2,4): 2382,
    (6,3,1): 2431, (6,3,2): 2479, (6,3,3): 2528, (6,3,4): 2576,
}


def get_rank_label(tier_idx: int, sub: int, div: int) -> str:
    tier = TIERS[tier_idx][1]
    return f"{tier} {sub} / Дивизион {div}"


def get_auto_mmr(tier_idx: int, sub: int, div: int) -> int:
    return RANK_MMR_TABLE.get((tier_idx, sub, div), 0)


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
            text=f"Дивизион {d}  (~{mmr} MMR)",
            callback_data=f"rd:{prefix}:{tier_idx}:{sub}:{d}"
        )])
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=f"rsb:{prefix}:{tier_idx}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
