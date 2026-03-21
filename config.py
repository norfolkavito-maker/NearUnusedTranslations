import os

TOKEN = os.getenv("TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@ebka_news")
GROUP_ID = int(os.getenv("GROUP_ID", -1001234567890))
MAX_PLAYERS = 64
