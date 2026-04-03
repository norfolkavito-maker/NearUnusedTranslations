import aiosqlite
import os
from config import TURSO_URL, TURSO_TOKEN

# Database Connection - временно вернем к SQLite
async def get_db_connection():
    """Подключение к базе данных"""
    try:
        # Пробуем разные пути для БД
        if os.path.exists("/app/data"):
            path = "/app/data/users.db"
            print("✅ Используем /app/data для БД")
        elif os.path.exists("/tmp"):
            path = "/tmp/users.db"
            print("✅ Используем /tmp для БД")
        elif os.path.exists("./"):
            path = "./users.db"
            print("✅ Используем локальную директорию для БД")
        else:
            path = ":memory:"
            print("⚠️ Используем in-memory БД")
        
        conn = await aiosqlite.connect(path)
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise

DB_CONNECTION = None

async def init_db():
    global DB_CONNECTION
    print(f"🗄️ Инициализация базы данных...")
    
    try:
        DB_CONNECTION = await get_db_connection()
        
        # Users table
        await DB_CONNECTION.execute("""
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
        await DB_CONNECTION.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Moderators table
        await DB_CONNECTION.execute("""
        CREATE TABLE IF NOT EXISTS moderators (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Channel settings table
        await DB_CONNECTION.execute("""
        CREATE TABLE IF NOT EXISTS channel_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            channel_link TEXT,
            discord_link TEXT,
            require_subscription BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tournaments table
        await DB_CONNECTION.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            date_time TEXT,
            max_players INTEGER,
            prize TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Welcome messages table
        await DB_CONNECTION.execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tournament notifications table
        await DB_CONNECTION.execute("""
        CREATE TABLE IF NOT EXISTS tournament_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            message TEXT,
            send_time TEXT,
            sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        await DB_CONNECTION.commit()
        print("✅ База данных инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        raise

# ── User Management ───────────────────────────────────────────────────────────────
async def add_user(tg_id, username="", epic="", discord="", rank="", peak_rank="", tracker=""):
    try:
        await DB_CONNECTION.execute(
            "INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tg_id, username, epic, discord, rank, peak_rank, tracker)
        )
        await DB_CONNECTION.commit()
        print(f"✅ Пользователь {tg_id} добавлен в БД")
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")

async def check_user(tg_id):
    try:
        cursor = await DB_CONNECTION.execute("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"❌ Ошибка проверки пользователя: {e}")
        return False

async def get_user(tg_id):
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        if row:
            columns = ["tg_id", "username", "epic", "discord", "rank", "peak_rank", "tracker"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return None

async def get_all_users():
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        columns = ["tg_id", "username", "epic", "discord", "rank", "peak_rank", "tracker"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения всех пользователей: {e}")
        return []

async def delete_user(tg_id):
    try:
        await DB_CONNECTION.execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        await DB_CONNECTION.commit()
        print(f"✅ Пользователь {tg_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления пользователя: {e}")

async def delete_all_users():
    try:
        await DB_CONNECTION.execute("DELETE FROM users")
        await DB_CONNECTION.commit()
        print("✅ Все пользователи удалены из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления всех пользователей: {e}")

async def count_users():
    try:
        cursor = await DB_CONNECTION.execute("SELECT COUNT(*) FROM users")
        count = await cursor.fetchone()
        return count[0] if count else 0
    except Exception as e:
        print(f"❌ Ошибка подсчета пользователей: {e}")
        return 0

# ── Admin Management ───────────────────────────────────────────────────────────────
async def add_admin(tg_id, username="", added_by=0):
    try:
        await DB_CONNECTION.execute(
            "INSERT OR REPLACE INTO admins (tg_id, username, added_by) VALUES (?, ?, ?)",
            (tg_id, username, added_by)
        )
        await DB_CONNECTION.commit()
        print(f"✅ Админ {tg_id} добавлен в БД")
    except Exception as e:
        print(f"❌ Ошибка добавления админа: {e}")

async def remove_admin(tg_id):
    try:
        await DB_CONNECTION.execute("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
        await DB_CONNECTION.commit()
        print(f"✅ Админ {tg_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления админа: {e}")

async def get_all_admins():
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM admins ORDER BY added_at DESC")
        rows = await cursor.fetchall()
        columns = ["tg_id", "username", "added_by", "added_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения админов: {e}")
        return []

async def is_admin_db(tg_id):
    try:
        cursor = await DB_CONNECTION.execute("SELECT tg_id FROM admins WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"❌ Ошибка проверки админа: {e}")
        return False

# ── Moderator Management ───────────────────────────────────────────────────────────
async def add_moderator(tg_id, username="", added_by=0):
    try:
        await DB_CONNECTION.execute(
            "INSERT OR REPLACE INTO moderators (tg_id, username, added_by) VALUES (?, ?, ?)",
            (tg_id, username, added_by)
        )
        await DB_CONNECTION.commit()
        print(f"✅ Модератор {tg_id} добавлен в БД")
    except Exception as e:
        print(f"❌ Ошибка добавления модератора: {e}")

async def remove_moderator(tg_id):
    try:
        await DB_CONNECTION.execute("DELETE FROM moderators WHERE tg_id = ?", (tg_id,))
        await DB_CONNECTION.commit()
        print(f"✅ Модератор {tg_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления модератора: {e}")

async def get_all_moderators():
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM moderators ORDER BY added_at DESC")
        rows = await cursor.fetchall()
        columns = ["tg_id", "username", "added_by", "added_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения модераторов: {e}")
        return []

async def is_moderator(tg_id):
    try:
        cursor = await DB_CONNECTION.execute("SELECT tg_id FROM moderators WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"❌ Ошибка проверки модератора: {e}")
        return False

async def is_admin_or_moderator(tg_id):
    return await is_admin_db(tg_id) or await is_moderator(tg_id)

# ── Channel Settings ───────────────────────────────────────────────────────────────
async def update_channel_settings(channel_link="", discord_link="", require_subscription=False):
    try:
        await DB_CONNECTION.execute(
            "INSERT OR REPLACE INTO channel_settings (id, channel_link, discord_link, require_subscription) VALUES (1, ?, ?, ?)",
            (channel_link, discord_link, require_subscription)
        )
        await DB_CONNECTION.commit()
        print("✅ Настройки канала обновлены")
    except Exception as e:
        print(f"❌ Ошибка обновления настроек канала: {e}")

async def get_channel_settings():
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM channel_settings WHERE id = 1")
        row = await cursor.fetchone()
        if row:
            columns = ["id", "channel_link", "discord_link", "require_subscription", "created_at"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения настроек канала: {e}")
        return None

# ── Tournament Management ───────────────────────────────────────────────────────────
async def add_tournament(name, description="", date_time="", max_players=0, prize=""):
    try:
        cursor = await DB_CONNECTION.execute(
            "INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)",
            (name, description, date_time, max_players, prize)
        )
        tournament_id = cursor.lastrowid
        await DB_CONNECTION.commit()
        print(f"✅ Турнир {tournament_id} добавлен в БД")
        return tournament_id
    except Exception as e:
        print(f"❌ Ошибка добавления турнира: {e}")
        return None

async def get_all_tournaments():
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM tournaments ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        columns = ["id", "name", "description", "date_time", "max_players", "prize", "created_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения турниров: {e}")
        return []

async def get_tournament(tournament_id):
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
        row = await cursor.fetchone()
        if row:
            columns = ["id", "name", "description", "date_time", "max_players", "prize", "created_at"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения турнира: {e}")
        return None

async def update_tournament(tournament_id, name=None, description=None, date_time=None, max_players=None, prize=None):
    try:
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if date_time is not None:
            updates.append("date_time = ?")
            params.append(date_time)
        if max_players is not None:
            updates.append("max_players = ?")
            params.append(max_players)
        if prize is not None:
            updates.append("prize = ?")
            params.append(prize)
        
        if updates:
            params.append(tournament_id)
            await DB_CONNECTION.execute(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", params)
            await DB_CONNECTION.commit()
            print(f"✅ Турнир {tournament_id} обновлен")
    except Exception as e:
        print(f"❌ Ошибка обновления турнира: {e}")

async def delete_tournament(tournament_id):
    try:
        await DB_CONNECTION.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        await DB_CONNECTION.commit()
        print(f"✅ Турнир {tournament_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления турнира: {e}")

# ── Welcome Message Management ───────────────────────────────────────────────────────
async def add_welcome_message(message):
    try:
        # Деактивируем все предыдущие сообщения
        await DB_CONNECTION.execute("UPDATE welcome_messages SET is_active = 0")
        
        # Добавляем новое активное сообщение
        cursor = await DB_CONNECTION.execute(
            "INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)",
            (message,)
        )
        message_id = cursor.lastrowid
        await DB_CONNECTION.commit()
        print(f"✅ Приветственное сообщение {message_id} добавлено")
        return message_id
    except Exception as e:
        print(f"❌ Ошибка добавления приветственного сообщения: {e}")
        return None

async def get_active_welcome_message():
    try:
        cursor = await DB_CONNECTION.execute("SELECT * FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        row = await cursor.fetchone()
        if row:
            columns = ["id", "message", "is_active", "created_at"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения активного приветственного сообщения: {e}")
        return None

async def update_welcome_message(message_id, message):
    try:
        await DB_CONNECTION.execute(
            "UPDATE welcome_messages SET message = ? WHERE id = ?",
            (message, message_id)
        )
        await DB_CONNECTION.commit()
        print(f"✅ Приветственное сообщение {message_id} обновлено")
    except Exception as e:
        print(f"❌ Ошибка обновления приветственного сообщения: {e}")

# ── Tournament Notifications Management ───────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    try:
        cursor = await DB_CONNECTION.execute(
            "INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)",
            (tournament_id, message, send_time)
        )
        notification_id = cursor.lastrowid
        await DB_CONNECTION.commit()
        print(f"✅ Уведомление {notification_id} добавлено")
        return notification_id
    except Exception as e:
        print(f"❌ Ошибка добавления уведомления: {e}")
        return None

async def get_pending_notifications():
    try:
        cursor = await DB_CONNECTION.execute(
            "SELECT * FROM tournament_notifications WHERE sent = 0 ORDER BY send_time ASC"
        )
        rows = await cursor.fetchall()
        columns = ["id", "tournament_id", "message", "send_time", "sent", "created_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения отложенных уведомлений: {e}")
        return []

async def mark_notification_sent(notification_id):
    try:
        await DB_CONNECTION.execute(
            "UPDATE tournament_notifications SET sent = 1 WHERE id = ?",
            (notification_id,)
        )
        await DB_CONNECTION.commit()
        print(f"✅ Уведомление {notification_id} отмечено как отправленное")
    except Exception as e:
        print(f"❌ Ошибка отметки уведомления как отправленного: {e}")
