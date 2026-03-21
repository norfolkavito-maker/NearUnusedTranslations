import os

TOKEN = os.getenv("TOKEN", "")

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    ADMIN_ID = 0

SECOND_ADMIN_ID = 6852512620
ADMIN_IDS = {ADMIN_ID, SECOND_ADMIN_ID}

CHANNEL_ID   = os.getenv("CHANNEL_ID", "@ebka_news")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", f"https://t.me/{os.getenv('CHANNEL_ID', 'ebka_news').lstrip('@')}")
GROUP_LINK   = os.getenv("GROUP_LINK", "")
