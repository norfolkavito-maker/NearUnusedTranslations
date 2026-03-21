import aiosqlite

DB_PATH = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            epic TEXT,
            discord TEXT,
            rank TEXT,
            peak_rank TEXT
        )
        """)
        await db.commit()

async def add_user(tg_id, epic="", discord="", rank="", peak_rank=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (tg_id, epic, discord, rank, peak_rank) VALUES (?, ?, ?, ?, ?)",
            (tg_id, epic, discord, rank, peak_rank)
        )
        await db.commit()

async def check_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,)) as cur:
            row = await cur.fetchone()
            return row is not None
