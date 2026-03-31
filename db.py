import aiosqlite
import os

DB_PATH = "/tmp/users.db"

async def init_db():
    # Создаем директорию если нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            epic TEXT,
            discord TEXT,
            rank TEXT,
            peak_rank TEXT,
            tracker TEXT
        )
        """)
        
        # Admins table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Channel settings table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS channel_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            channel_link TEXT,
            discord_link TEXT,
            require_subscription BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tournaments table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            date_time TEXT NOT NULL,
            max_players INTEGER,
            prize TEXT,
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Welcome messages table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tournament notifications table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS tournament_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            message TEXT NOT NULL,
            send_time TEXT NOT NULL,
            is_sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
        )
        """)
        
        # Add missing columns to users table
        for col in ("username", "tracker"):
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            except Exception:
                pass
        
        await db.commit()

# ── User Management ───────────────────────────────────────────────────────────────
async def add_user(tg_id, username="", epic="", discord="", rank="", peak_rank="", tracker=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tg_id, username, epic, discord, rank, peak_rank, tracker)
        )
        await db.commit()

async def check_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,)) as cur:
            row = await cur.fetchone()
            return row is not None

async def get_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

async def delete_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        await db.commit()

async def delete_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users")
        await db.commit()

async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0]

# ── Admin Management ─────────────────────────────────────────────────────────────
async def add_admin(tg_id: int, username: str = "", added_by: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins (tg_id, username, added_by) VALUES (?, ?, ?)",
            (tg_id, username, added_by)
        )
        await db.commit()

async def remove_admin(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
        await db.commit()

async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins ORDER BY added_at") as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

async def is_admin_db(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT tg_id FROM admins WHERE tg_id = ?", (tg_id,)) as cur:
            row = await cur.fetchone()
            return row is not None

# ── Channel Settings Management ───────────────────────────────────────────────────
async def update_channel_settings(channel_link: str = None, discord_link: str = None, require_subscription: bool = None):
    async with aiosqlite.connect(DB_PATH) as db:
        updates = []
        values = []
        if channel_link is not None:
            updates.append("channel_link = ?")
            values.append(channel_link)
        if discord_link is not None:
            updates.append("discord_link = ?")
            values.append(discord_link)
        if require_subscription is not None:
            updates.append("require_subscription = ?")
            values.append(require_subscription)
        values.append(1)  # id = 1
        await db.execute(f"UPDATE channel_settings SET {', '.join(updates)} WHERE id = ?", values)
        await db.commit()

async def get_channel_settings():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channel_settings WHERE id = 1") as cur:
            row = await cur.fetchone()
            return dict(row) if row else {"channel_link": "", "discord_link": "", "require_subscription": False}

# ── Tournament Management ───────────────────────────────────────────────────────
async def add_tournament(name, description="", date_time="", max_players=None, prize=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)",
            (name, description, date_time, max_players, prize)
        )
        await db.commit()

async def get_all_tournaments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tournaments ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

async def get_tournament(tournament_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def update_tournament(tournament_id, name=None, description=None, date_time=None, max_players=None, prize=None, status=None):
    async with aiosqlite.connect(DB_PATH) as db:
        updates = []
        values = []
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if date_time is not None:
            updates.append("date_time = ?")
            values.append(date_time)
        if max_players is not None:
            updates.append("max_players = ?")
            values.append(max_players)
        if prize is not None:
            updates.append("prize = ?")
            values.append(prize)
        if status is not None:
            updates.append("status = ?")
            values.append(status)
        
        values.append(tournament_id)
        await db.execute(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", values)
        await db.commit()

async def delete_tournament(tournament_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        await db.commit()

# ── Welcome Message Management ───────────────────────────────────────────────────
async def add_welcome_message(message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO welcome_messages (message) VALUES (?)", (message,))
        await db.commit()

async def get_active_welcome_message():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT message FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1") as cur:
            row = await cur.fetchone()
            return row["message"] if row else None

async def update_welcome_message(message):
    async with aiosqlite.connect(DB_PATH) as db:
        # Deactivate all messages
        await db.execute("UPDATE welcome_messages SET is_active = 0")
        # Add new message
        await db.execute("INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)", (message,))
        await db.commit()

# ── Notification Management ───────────────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)",
            (tournament_id, message, send_time)
        )
        await db.commit()

async def get_pending_notifications():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tournament_notifications WHERE is_sent = 0 ORDER BY send_time") as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

async def mark_notification_sent(notification_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tournament_notifications SET is_sent = 1 WHERE id = ?", (notification_id,))
        await db.commit()
