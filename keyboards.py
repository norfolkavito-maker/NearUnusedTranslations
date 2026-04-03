from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎮 Регистрация"), KeyboardButton(text="📋 Мои данные")],
        [KeyboardButton(text="🗑 Удалить мои данные"), KeyboardButton(text="💬 Обратиться к админам")],
        [KeyboardButton(text="🎮 Discord")]
    ],
    resize_keyboard=True
)

kb_admin_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎮 Регистрация"), KeyboardButton(text="📋 Мои данные")],
        [KeyboardButton(text="🗑 Удалить мои данные"), KeyboardButton(text="⚙️ Админ-панель")],
        [KeyboardButton(text="💬 Обратиться к админам"), KeyboardButton(text="🎮 Discord")]
    ],
    resize_keyboard=True
)

kb_delete_confirm = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Да, удалить", callback_data="delete_self:yes")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="delete_self:no")],
])

TIERS = [
    ("🟫 Бронза", "Бронза", "-100–643"),
    ("⬜ Серебро", "Серебро", "295–577"),
    ("🟨 Золото", "Золото", "475–643"),
    ("🟦 Платина", "Платина", "655–825"),
    ("💎 Даймонд", "Даймонд", "835–1060"),
    ("🏆 Чемпион", "Чемпион", "1075–1420"),
    ("👑 ГЧ", "Гранд-Чемпион", "1435–1859"),
    ("⚡ SSL", "SSL", "1873–1941"),
]

# Simplified MMR table for new structure
RANK_MMR_TABLE = {
    # Bronze (tier_idx 0)
    (0,1,1): 100,  (0,1,2): 126,  (0,1,3): 139,  (0,1,4): 157,
    (0,2,1): 168,  (0,2,2): 180,  (0,2,3): 198,  (0,2,4): 217,
    (0,3,1): 232,  (0,3,2): 240,  (0,3,3): 258,  (0,3,4): 277,
    # Silver (tier_idx 1)
    (1,1,1): 295,  (1,1,2): 299,  (1,1,3): 318,  (1,1,4): 337,
    (1,2,1): 355,  (1,2,2): 359,  (1,2,3): 378,  (1,2,4): 397,
    (1,3,1): 414,  (1,3,2): 419,  (1,3,3): 438,  (1,3,4): 457,
    # Gold (tier_idx 2)
    (2,1,1): 475,  (2,1,2): 479,  (2,1,3): 498,  (2,1,4): 517,
    (2,2,1): 535,  (2,2,2): 539,  (2,2,3): 558,  (2,2,4): 577,
    (2,3,1): 595,  (2,3,2): 599,  (2,3,3): 618,  (2,3,4): 637,
    # Platinum (tier_idx 3)
    (3,1,1): 655,  (3,1,2): 659,  (3,1,3): 678,  (3,1,4): 697,
    (3,2,1): 715,  (3,2,2): 719,  (3,2,3): 738,  (3,2,4): 757,
    (3,3,1): 773,  (3,3,2): 779,  (3,3,3): 798,  (3,3,4): 817,
    # Diamond (tier_idx 4)
    (4,1,1): 835,  (4,1,2): 845,  (4,1,3): 873,  (4,1,4): 892,
    (4,2,1): 915,  (4,2,2): 925,  (4,2,3): 948,  (4,2,4): 972,
    (4,3,1): 995,  (4,3,2): 1005, (4,3,3): 1028, (4,3,4): 1052,
    # Champion (tier_idx 5)
    (5,1,1): 1075, (5,1,2): 1095, (5,1,3): 1128, (5,1,4): 1162,
    (5,2,1): 1195, (5,2,2): 1215, (5,2,3): 1248, (5,2,4): 1282,
    (5,3,1): 1315, (5,3,2): 1335, (5,3,3): 1372, (5,3,4): 1402,
    # Grand Champion (tier_idx 6)
    (6,1,1): 1435, (6,1,2): 1460, (6,1,3): 1500, (6,1,4): 1537,
    (6,2,1): 1575, (6,2,2): 1602, (6,2,3): 1647, (6,2,4): 1677,
    (6,3,1): 1714, (6,3,2): 1745, (6,3,3): 1788, (6,3,4): 1832,
    # SSL (tier_idx 7)
    (7,1,1): 1873, (7,1,2): 1900, (7,1,3): 1925, (7,1,4): 1950,
    (7,2,1): 2000, (7,2,2): 2025, (7,2,3): 2050, (7,2,4): 2075,
    (7,3,1): 2100, (7,3,2): 2125, (7,3,3): 2150, (7,3,4): 2175,
}

def get_rank_label(tier_idx: int, sub: int, div: int) -> str:
    tier_names = ["Бронза", "Серебро", "Золото", "Платина", "Даймонд", "Чемпион", "ГЧ", "SSL"]
    tier_name = tier_names[tier_idx] if tier_idx < len(tier_names) else "Unknown"
    if tier_idx == 6:  # Grand Champion
        return f"ГЧ{sub}"
    return f"{tier_name} {sub} / Дивизион {div}"

def get_auto_mmr(tier_idx: int, sub: int, div: int) -> int:
    return RANK_MMR_TABLE.get((tier_idx, sub, div), 0)

def get_mmr_range(tier_idx: int, sub: int, div: int) -> str:
    """Возвращает MMR диапазон для ранга"""
    mmr = get_auto_mmr(tier_idx, sub, div)
    
    # Определяем диапазон на основе позиции в таблице
    if tier_idx == 6:  # Grand Champion
        ranges = {
            (6,1,1): "1435-1460", (6,1,2): "1460-1500", (6,1,3): "1500-1537", (6,1,4): "1537-1575",
            (6,2,1): "1575-1602", (6,2,2): "1602-1647", (6,2,3): "1647-1677", (6,2,4): "1677-1714",
            (6,3,1): "1714-1745", (6,3,2): "1745-1788", (6,3,3): "1788-1832", (6,3,4): "1832-1873"
        }
        return ranges.get((tier_idx, sub, div), "1435-1873")
    else:
        # Для остальных рангов определяем диапазон +-15 MMR
        return f"{mmr-15}-{mmr+15}"

def kb_sub_check(channel_link: str, group_link: str = "") -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="📢 Подписаться на канал", url=channel_link)]]
    if group_link:
        buttons.append([InlineKeyboardButton(text="👥 Вступить в группу", url=group_link)])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался — проверить", callback_data="sub_check")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

kb_admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋 Список участников", callback_data="adm:list")],
    [InlineKeyboardButton(text="🎮 Удобный список игроков", callback_data="adm:players")],
    [InlineKeyboardButton(text="👥 Управление админами", callback_data="adm:admins")],
    [InlineKeyboardButton(text="📢 Настройки канала", callback_data="adm:channel")],
    [InlineKeyboardButton(text="🏆 Управление турнирами", callback_data="adm:tournaments")],
    [InlineKeyboardButton(text="📝 Приветственное сообщение", callback_data="adm:welcome")],
    [InlineKeyboardButton(text="📝 Сообщение после регистрации", callback_data="adm:post_reg_msg")],
    [InlineKeyboardButton(text="⚙️ Настройки регистрации", callback_data="adm:reg_settings")],
    [InlineKeyboardButton(text="📢 Рассылки", callback_data="adm:notifications")],
    [
        InlineKeyboardButton(text="🗑 Удалить игрока", callback_data="adm:kick"),
        InlineKeyboardButton(text="💥 Удалить всех", callback_data="adm:deleteall"),
    ],
])

kb_admin_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin:add")],
    [InlineKeyboardButton(text="🗑 Удалить админа", callback_data="admin:remove")],
    [InlineKeyboardButton(text="📋 Список админов", callback_data="admin:list")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
])

kb_channel_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Изменить ссылку канала", callback_data="channel:edit")],
    [InlineKeyboardButton(text="🎮 Изменить Discord ссылку", callback_data="channel:discord")],
    [InlineKeyboardButton(text="🔔 Требовать подписку", callback_data="channel:toggle")],
    [InlineKeyboardButton(text="👀 Посмотреть настройки", callback_data="channel:view")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
])

kb_tournament_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Создать турнир", callback_data="tour:create")],
    [InlineKeyboardButton(text="📋 Список турниров", callback_data="tour:list")],
    [InlineKeyboardButton(text="🔔 Настроить уведомления", callback_data="tour:notifications")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
])

kb_welcome_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Изменить сообщение", callback_data="wel:edit")],
    [InlineKeyboardButton(text="👀 Посмотреть текущее", callback_data="wel:view")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
])

kb_post_reg_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Изменить сообщение", callback_data="postreg:edit")],
    [InlineKeyboardButton(text="👀 Посмотреть текущее", callback_data="postreg:view")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
])

kb_reg_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Epic ID", callback_data="regset:epic")],
    [InlineKeyboardButton(text="✅ Discord", callback_data="regset:discord")],
    [InlineKeyboardButton(text="✅ Актуальный MMR", callback_data="regset:rank")],
    [InlineKeyboardButton(text="✅ Пиковый MMR", callback_data="regset:peak_rank")],
    [InlineKeyboardButton(text="✅ RL Tracker", callback_data="regset:tracker")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
])

kb_notifications_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Создать рассылку", callback_data="notif:create")],
    [InlineKeyboardButton(text="📢 Рассылка всем пользователям", callback_data="notif:broadcast")],
    [InlineKeyboardButton(text="📋 Отложенные рассылки", callback_data="notif:list")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
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

# ── SuperUser Keyboards ───────────────────────────────────────────────────────────────
kb_superuser_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Логи активности", callback_data="su:activity_logs")],
    [InlineKeyboardButton(text="📝 Логи бота", callback_data="su:bot_logs")],
    [InlineKeyboardButton(text="👥 Все пользователи", callback_data="su:all_users")],
    [InlineKeyboardButton(text="💾 Создать бэкап", callback_data="su:backup")],
    [InlineKeyboardButton(text="📂 Восстановить из бэкапа", callback_data="su:restore")],
    [InlineKeyboardButton(text="⚙️ Войти в админ-панель", callback_data="su:admin_panel")],
    [InlineKeyboardButton(text="🔑 Сменить пароль", callback_data="su:change_password")],
    [InlineKeyboardButton(text="🧹 Очистить логи", callback_data="su:clear_logs")],
    [InlineKeyboardButton(text="📈 Общая статистика", callback_data="su:stats")],
    [InlineKeyboardButton(text="🚪 Выйти", callback_data="su:exit")],
])

kb_superuser_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ Назад", callback_data="su:back")],
])

kb_clear_logs_confirm = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🗑 Очистить всё", callback_data="su:clear_confirm")],
    [InlineKeyboardButton(text="◀️ Отмена", callback_data="su:back")],
])
