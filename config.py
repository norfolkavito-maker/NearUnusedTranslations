import os

TOKEN = os.getenv("TOKEN", "")
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    ADMIN_ID = 0
CHANNEL_ID = os.getenv("CHANNEL_ID", "@ebka_news")
GROUP_ID = int(os.getenv("GROUP_ID", -1001234567890))
