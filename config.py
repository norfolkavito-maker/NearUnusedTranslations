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

# Turso Database
TURSO_URL = os.getenv("TURSO_URL", "libsql://bot-mmmmmm.aws-eu-west-1.turso.io")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzQ5ODcxOTYsImlkIjoiMDE5ZDQ1NzMtNjEwMS03MjRkLWJhMjQtZTIwNTNjMDJhMmJhIiwicmlkIjoiZjM5OWIyOTktNWJlYi00NzFmLWIwZWEtMGE1NzI1YTkyOWExIn0.IHWIH6wqBrsw1jvCkCDkdAikwpvSBJxLP8g4jtC3q7e2-7RAVu0u0u58sz90AaawsD1yK-L5gxSoIJYlXDf4Dw")
