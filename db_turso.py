import os
from libsql_client import create_client

# Turso connection
DATABASE_URL = os.getenv("DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

client = None

def get_client():
    global client
    if client is None:
        if DATABASE_URL:
            client = create_client(DATABASE_URL, auth_token=TURSO_TOKEN)
        else:
            # Fallback to local SQLite
            client = create_client("file:users.db")
    return client

async def init_db():
    db = get_client()
    
    # Create tables
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
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS channel_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            channel_link TEXT,
            discord_link TEXT,
            require_subscription INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            date_time TEXT NOT NULL,
            max_players INTEGER,
            prize TEXT,
            status TEXT DEFAULT 'upcoming',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS tournament_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            message TEXT NOT NULL,
            send_time TEXT NOT NULL,
            is_sent INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
        )
    """)

# ── User Management ───────────────────────────────────────────────────────────────
async def add_user(tg_id, username="", epic="", discord="", rank="", peak_rank="", tracker=""):
    db = get_client()
    await db.execute(
        "INSERT OR REPLACE INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [tg_id, username, epic, discord, rank, peak_rank, tracker]
    )

async def check_user(tg_id):
    db = get_client()
    result = await db.execute("SELECT tg_id FROM users WHERE tg_id = ?", [tg_id])
    return len(result) > 0

async def get_user(tg_id):
    db = get_client()
    result = await db.execute("SELECT * FROM users WHERE tg_id = ?", [tg_id])
    if result:
        row = result[0]
        return {
            'tg_id': row[0], 'username': row[1], 'epic': row[2], 
            'discord': row[3], 'rank': row[4], 'peak_rank': row[5], 'tracker': row[6]
        }
    return None

async def get_all_users():
    db = get_client()
    result = await db.execute("SELECT * FROM users")
    return [
        {
            'tg_id': row[0], 'username': row[1], 'epic': row[2], 
            'discord': row[3], 'rank': row[4], 'peak_rank': row[5], 'tracker': row[6]
        }
        for row in result
    ]

async def delete_user(tg_id):
    db = get_client()
    await db.execute("DELETE FROM users WHERE tg_id = ?", [tg_id])

async def delete_all_users():
    db = get_client()
    await db.execute("DELETE FROM users")

async def count_users():
    db = get_client()
    result = await db.execute("SELECT COUNT(*) FROM users")
    return result[0][0]

# ── Admin Management ─────────────────────────────────────────────────────────────
async def add_admin(tg_id: int, username: str = "", added_by: int = None):
    db = get_client()
    await db.execute(
        "INSERT OR REPLACE INTO admins (tg_id, username, added_by) VALUES (?, ?, ?)",
        [tg_id, username, added_by]
    )

async def remove_admin(tg_id: int):
    db = get_client()
    await db.execute("DELETE FROM admins WHERE tg_id = ?", [tg_id])

async def get_all_admins():
    db = get_client()
    result = await db.execute("SELECT * FROM admins ORDER BY added_at")
    return [
        {
            'tg_id': row[0], 'username': row[1], 'added_by': row[2], 'added_at': row[3]
        }
        for row in result
    ]

async def is_admin_db(tg_id: int):
    db = get_client()
    result = await db.execute("SELECT tg_id FROM admins WHERE tg_id = ?", [tg_id])
    return len(result) > 0

# ── Channel Settings Management ───────────────────────────────────────────────────
async def update_channel_settings(channel_link: str = None, discord_link: str = None, require_subscription: bool = None):
    db = get_client()
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
        values.append(1 if require_subscription else 0)
    
    values.append(1)  # id = 1
    await db.execute(f"UPDATE channel_settings SET {', '.join(updates)} WHERE id = ?", values)

async def get_channel_settings():
    db = get_client()
    result = await db.execute("SELECT * FROM channel_settings WHERE id = 1")
    if result:
        row = result[0]
        return {
            'channel_link': row[1] or '', 'discord_link': row[2] or '', 
            'require_subscription': bool(row[3])
        }
    return {"channel_link": "", "discord_link": "", "require_subscription": False}

# ── Tournament Management ───────────────────────────────────────────────────────
async def add_tournament(name, description="", date_time="", max_players=None, prize=""):
    db = get_client()
    db.execute(
        "INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)",
        [name, description, date_time, max_players, prize]
    )

async def get_all_tournaments():
    db = get_client()
    result = db.execute("SELECT * FROM tournaments ORDER BY created_at DESC")
    return [
        {
            'id': row[0], 'name': row[1], 'description': row[2], 'date_time': row[3],
            'max_players': row[4], 'prize': row[5], 'status': row[6], 'created_at': row[7]
        }
        for row in result
    ]

async def get_tournament(tournament_id):
    db = get_client()
    result = db.execute("SELECT * FROM tournaments WHERE id = ?", [tournament_id])
    if result:
        row = result[0]
        return {
            'id': row[0], 'name': row[1], 'description': row[2], 'date_time': row[3],
            'max_players': row[4], 'prize': row[5], 'status': row[6], 'created_at': row[7]
        }
    return None

async def update_tournament(tournament_id, name=None, description=None, date_time=None, max_players=None, prize=None, status=None):
    db = get_client()
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
    db.execute(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", values)

async def delete_tournament(tournament_id):
    db = get_client()
    db.execute("DELETE FROM tournaments WHERE id = ?", [tournament_id])

# ── Welcome Message Management ───────────────────────────────────────────────────
async def add_welcome_message(message):
    db = get_client()
    db.execute("INSERT INTO welcome_messages (message) VALUES (?)", [message])

async def get_active_welcome_message():
    db = get_client()
    result = db.execute("SELECT message FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
    return result[0][0] if result else None

async def update_welcome_message(message):
    db = get_client()
    db.execute("UPDATE welcome_messages SET is_active = 0")
    db.execute("INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)", [message])

# ── Notification Management ───────────────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    db = get_client()
    db.execute(
        "INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)",
        [tournament_id, message, send_time]
    )

async def get_pending_notifications():
    db = get_client()
    result = db.execute("SELECT * FROM tournament_notifications WHERE is_sent = 0 ORDER BY send_time")
    return [
        {
            'id': row[0], 'tournament_id': row[1], 'message': row[2],
            'send_time': row[3], 'is_sent': bool(row[4]), 'created_at': row[5]
        }
        for row in result
    ]

async def mark_notification_sent(notification_id):
    db = get_client()
    db.execute("UPDATE tournament_notifications SET is_sent = 1 WHERE id = ?", [notification_id])
# ── Tournament Management ───────────────────────────────────────────────────────
async def add_tournament(name, description="", date_time="", max_players=None, prize=""):
    db = get_client()
    await db.execute(
        "INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)",
        [name, description, date_time, max_players, prize]
    )

async def get_all_tournaments():
    db = get_client()
    result = await db.execute("SELECT * FROM tournaments ORDER BY created_at DESC")
    return [
        {
            'id': row[0], 'name': row[1], 'description': row[2], 'date_time': row[3],
            'max_players': row[4], 'prize': row[5], 'status': row[6], 'created_at': row[7]
        }
        for row in result
    ]

async def get_tournament(tournament_id):
    db = get_client()
    result = await db.execute("SELECT * FROM tournaments WHERE id = ?", [tournament_id])
    if result:
        row = result[0]
        return {
            'id': row[0], 'name': row[1], 'description': row[2], 'date_time': row[3],
            'max_players': row[4], 'prize': row[5], 'status': row[6], 'created_at': row[7]
        }
    return None

async def update_tournament(tournament_id, name=None, description=None, date_time=None, max_players=None, prize=None, status=None):
    db = get_client()
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

async def delete_tournament(tournament_id):
    db = get_client()
    await db.execute("DELETE FROM tournaments WHERE id = ?", [tournament_id])

# ── Welcome Message Management ───────────────────────────────────────────────────
async def add_welcome_message(message):
    db = get_client()
    await db.execute("INSERT INTO welcome_messages (message) VALUES (?)", [message])

async def get_active_welcome_message():
    db = get_client()
    result = await db.execute("SELECT message FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
    return result[0][0] if result else None

async def update_welcome_message(message):
    db = get_client()
    await db.execute("UPDATE welcome_messages SET is_active = 0")
    await db.execute("INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)", [message])

# ── Notification Management ───────────────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    db = get_client()
    await db.execute(
        "INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)",
        [tournament_id, message, send_time]
    )

async def get_pending_notifications():
    db = get_client()
    result = await db.execute("SELECT * FROM tournament_notifications WHERE is_sent = 0 ORDER BY send_time")
    return [
        {
            'id': row[0], 'tournament_id': row[1], 'message': row[2],
            'send_time': row[3], 'is_sent': bool(row[4]), 'created_at': row[5]
        }
        for row in result
    ]

async def mark_notification_sent(notification_id):
    db = get_client()
    await db.execute("UPDATE tournament_notifications SET is_sent = 1 WHERE id = ?", [notification_id])
