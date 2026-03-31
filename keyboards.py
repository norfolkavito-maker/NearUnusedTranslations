from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Полная таблица рангов с дивизионами и MMR
TIERS = [
    (0, "Bronze", [
        (0, "Bronze I", [
            (0, "Div I", (-100, 118)),
            (1, "Div II", (126, 137)),
            (2, "Div III", (139, 156)),
            (3, "Div IV", (157, 172)),
        ]),
        (1, "Bronze II", [
            (0, "Div I", (168, 178)),
            (1, "Div II", (180, 197)),
            (2, "Div III", (198, 215)),
            (3, "Div IV", (217, 226)),
        ]),
        (2, "Bronze III", [
            (0, "Div I", (232, 238)),
            (1, "Div II", (240, 257)),
            (2, "Div III", (258, 276)),
            (3, "Div IV", (277, 292)),
        ]),
    ]),
    (1, "Silver", [
        (0, "Silver I", [
            (0, "Div I", (295, 298)),
            (1, "Div II", (299, 317)),
            (2, "Div III", (318, 336)),
            (3, "Div IV", (337, 349)),
        ]),
        (1, "Silver II", [
            (0, "Div I", (355, 358)),
            (1, "Div II", (359, 377)),
            (2, "Div III", (378, 396)),
            (3, "Div IV", (397, 411)),
        ]),
        (2, "Silver III", [
            (0, "Div I", (414, 418)),
            (1, "Div II", (419, 437)),
            (2, "Div III", (438, 456)),
            (3, "Div IV", (457, 465)),
        ]),
    ]),
    (2, "Gold", [
        (0, "Gold I", [
            (0, "Div I", (475, 478)),
            (1, "Div II", (479, 497)),
            (2, "Div III", (498, 516)),
            (3, "Div IV", (517, 526)),
        ]),
        (1, "Gold II", [
            (0, "Div I", (535, 538)),
            (1, "Div II", (539, 557)),
            (2, "Div III", (558, 576)),
            (3, "Div IV", (577, 584)),
        ]),
        (2, "Gold III", [
            (0, "Div I", (595, 598)),
            (1, "Div II", (599, 617)),
            (2, "Div III", (618, 636)),
            (3, "Div IV", (637, 643)),
        ]),
    ]),
    (3, "Platinum", [
        (0, "Platinum I", [
            (0, "Div I", (655, 658)),
            (1, "Div II", (659, 677)),
            (2, "Div III", (678, 696)),
            (3, "Div IV", (697, 705)),
        ]),
        (1, "Platinum II", [
            (0, "Div I", (715, 718)),
            (1, "Div II", (719, 737)),
            (2, "Div III", (738, 756)),
            (3, "Div IV", (757, 764)),
        ]),
        (2, "Platinum III", [
            (0, "Div I", (773, 778)),
            (1, "Div II", (779, 797)),
            (2, "Div III", (798, 816)),
            (3, "Div IV", (817, 825)),
        ]),
    ]),
    (4, "Diamond", [
        (0, "Diamond I", [
            (0, "Div I", (835, 843)),
            (1, "Div II", (845, 867)),
            (2, "Div III", (873, 886)),
            (3, "Div IV", (892, 901)),
        ]),
        (1, "Diamond II", [
            (0, "Div I", (915, 923)),
            (1, "Div II", (925, 947)),
            (2, "Div III", (948, 969)),
            (3, "Div IV", (972, 980)),
        ]),
        (2, "Diamond III", [
            (0, "Div I", (995, 1003)),
            (1, "Div II", (1005, 1027)),
            (2, "Div III", (1028, 1049)),
            (3, "Div IV", (1052, 1060)),
        ]),
    ]),
    (5, "Champion", [
        (0, "Champion I", [
            (0, "Div I", (1075, 1093)),
            (1, "Div II", (1095, 1114)),
            (2, "Div III", (1128, 1154)),
            (3, "Div IV", (1162, 1180)),
        ]),
        (1, "Champion II", [
            (0, "Div I", (1195, 1213)),
            (1, "Div II", (1215, 1246)),
            (2, "Div III", (1248, 1274)),
            (3, "Div IV", (1282, 1300)),
        ]),
        (2, "Champion III", [
            (0, "Div I", (1315, 1333)),
            (1, "Div II", (1335, 1367)),
            (2, "Div III", (1372, 1393)),
            (3, "Div IV", (1402, 1420)),
        ]),
    ]),
    (6, "Grand Champion", [
        (0, "Grand Champion I", [
            (0, "Div I", (1435, 1458)),
            (1, "Div II", (1460, 1494)),
            (2, "Div III", (1500, 1522)),
            (3, "Div IV", (1537, 1559)),
        ]),
        (1, "Grand Champion II", [
            (0, "Div I", (1575, 1598)),
            (1, "Div II", (1602, 1637)),
            (2, "Div III", (1647, 1660)),
            (3, "Div IV", (1677, 1698)),
        ]),
        (2, "Grand Champion III", [
            (0, "Div I", (1714, 1736)),
            (1, "Div II", (1745, 1776)),
            (2, "Div III", (1788, 1814)),
            (3, "Div IV", (1832, 1859)),
        ]),
    ]),
    (7, "SSL", [
        (0, "Supersonic Legend", [
            (0, "Div I", (1873, 1941)),
        ]),
    ]),
]


def get_rank_label(tier_idx: int, sub: int, div: int) -> str:
    """Получить название ранга по индексам"""
    tier = TIERS[tier_idx]
    tier_name = tier[1]
    subtier = tier[2][sub]
    subtier_name = subtier[1]
    division = subtier[2][div]
    return f"{tier_name} {subtier_name} {division[1]}"


def get_auto_mmr(tier_idx: int, sub: int, div: int) -> int:
    """Получить среднее MMR для дивизиона"""
    tier = TIERS[tier_idx]
    subtier = tier[2][sub]
    division = subtier[2][div]
    mmr_range = division[3]
    return (mmr_range[0] + mmr_range[1]) // 2


def kb_main():
    """Основная клавиатура для пользователя"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Регистрация")],
            [KeyboardButton(text="📋 Мои данные")],
        ],
        resize_keyboard=True
    )


def kb_admin_main():
    """Админская клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Регистрация")],
            [KeyboardButton(text="📋 Мои данные")],
            [KeyboardButton(text="⚙️ Админ-панель")],
        ],
        resize_keyboard=True
    )


def kb_tiers(prefix: str):
    """Выбор тира (первого уровня ранга)"""
    buttons = []
    for tier_idx, tier_name, _ in TIERS:
        callback_data = f"rt:{prefix}:{tier_idx}"
        buttons.append([InlineKeyboardButton(text=tier_name, callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_subtiers(prefix: str, tier_idx: int):
    """Выбор подтира (второго уровня)"""
    tier = TIERS[tier_idx]
    buttons = []
    for sub_idx, subtier_name, _ in tier[2]:
        callback_data = f"rs:{prefix}:{tier_idx}:{sub_idx}"
        buttons.append([InlineKeyboardButton(text=subtier_name, callback_data=callback_data)])
    
    back_button = InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rb:{prefix}")
    buttons.append([back_button])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_divisions(prefix: str, tier_idx: int, sub_idx: int):
    """Выбор дивизиона"""
    tier = TIERS[tier_idx]
    subtier = tier[2][sub_idx]
    buttons = []
    for div_idx, div_name, mmr_range in subtier[2]:
        callback_data = f"rd:{prefix}:{tier_idx}:{sub_idx}:{div_idx}"
        buttons.append([InlineKeyboardButton(text=div_name, callback_data=callback_data)])
    
    # Опция ввода вручную
    buttons.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data=f"rm:{prefix}")])
    
    # Кнопка назад
    back_button = InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rsb:{prefix}:{tier_idx}")
    buttons.append([back_button])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_sub_check(channel_link: str, group_link: str = None):
    """Проверка подписки"""
    buttons = []
    if channel_link:
        buttons.append([InlineKeyboardButton(text="📢 Канал", url=channel_link)])
    if group_link:
        buttons.append([InlineKeyboardButton(text="👥 Группа", url=group_link)])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался!", callback_data="sub_check")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_admin_panel():
    """Админская панель"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Список участников", callback_data="adm:list")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats")],
            [InlineKeyboardButton(text="🗑 Удалить участника", callback_data="adm:kick")],
            [InlineKeyboardButton(text="💥 Удалить всех", callback_data="adm:deleteall")],
        ]
    )


def kb_deleteall_confirm():
    """Подтверждение удаления всех"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data="adm:deleteall_yes")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel")],
        ]
    )