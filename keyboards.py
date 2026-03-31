from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Main keyboard definition


async def kb_main():
    # Define the main keyboard layout
    pass


async def kb_admin_main():
    # Define the admin keyboard layout
    pass


TIERS = [
    {'label': 'Bronze', 'mmr_range': (-100, 199)},
    {'label': 'Silver', 'mmr_range': (200, 799)},
    {'label': 'Gold', 'mmr_range': (800, 1399)},
    {'label': 'Platinum', 'mmr_range': (1400, 1799)},
    {'label': 'Diamond', 'mmr_range': (1800, 2199)},
    {'label': 'Champion', 'mmr_range': (2200, 2599)},
    {'label': 'Grand Champion', 'mmr_range': (2600, 2999)},
    {'label': 'SSL', 'mmr_range': (3000, 1941)},
]


RANK_MMR_TABLE = {
    'Bronze': (-100, 199),
    'Silver': (200, 799),
    'Gold': (800, 1399),
    'Platinum': (1400, 1799),
    'Diamond': (1800, 2199),
    'Champion': (2200, 2599),
    'Grand Champion': (2600, 2999),
    'SSL': (3000, 1941),
}


def get_rank_label(mmr):
    for tier in TIERS:
        if tier['mmr_range'][0] <= mmr <= tier['mmr_range'][1]:
            return tier['label']
    return 'Unranked'


def get_auto_mmr():
    # Logic to automatically determine MMR
    pass


def kb_sub_check():
    # Function to check subscription
    pass


def kb_admin_panel():
    # Define the admin panel keyboard
    pass


def kb_deleteall_confirm():
    # Confirmation for deleting all
    pass


def kb_tiers():
    # Function returning available tiers
    pass


def kb_subtiers():
    # Function returning subtier information
    pass


def kb_divisions():
    # Function returning divisions
    pass