import aiosqlite
import os
import asyncio
from config import TURSO_URL, TURSO_TOKEN

# Database Connection - используем Turso для постоянного хранения
DB_CONNECTION = None
USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

async def get_db_connection():
    """Подключение к базе данных - Turso или SQLite fallback"""
    try:
        if USE_TURSO:
            print(f"🔗 Подключение к Turso: {TURSO_URL}")
            import libsql_experimental
            conn = libsql_experimental.connect(TURSO_URL, auth_token=TURSO_TOKEN)
            return conn
        else:
            # Fallback to SQLite с постоянным хранением
            if os.path.exists("/app/data"):
                path = "/app/data/users.db"
                print("✅ Используем /app/data для БД")
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

async def _execute(sql, params=()):
    """Execute SQL with proper sync/async handling"""
    global DB_CONNECTION
    if USE_TURSO:
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, lambda: DB_CONNECTION.execute(sql, params))
        return cursor
    else:
        return await DB_CONNECTION.execute(sql, params)

async def _commit():
    """Commit with proper sync/async handling"""
    global DB_CONNECTION
    if USE_TURSO:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, DB_CONNECTION.commit)
    else:
        await DB_CONNECTION.commit()

async def _fetchone(cursor):
    """Fetch one row with proper sync/async handling"""
    if USE_TURSO:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cursor.fetchone)
    else:
        return await cursor.fetchone()

async def _fetchall(cursor):
    """Fetch all rows with proper sync/async handling"""
    if USE_TURSO:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cursor.fetchall)
    else:
        return await cursor.fetchall()

async def init_db():
    global DB_CONNECTION
    print(f"🗄️ Инициализация базы данных... Turso: {USE_TURSO}")
    
    try:
        DB_CONNECTION = await get_db_connection()
        
        # Users table
        await _execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            epic TEXT,
            discord TEXT,
            rank TEXT,
            peak_rank TEXT,
            tracker TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Admins table
        await _execute("""
        CREATE TABLE IF NOT EXISTS admins (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Moderators table
        await _execute("""
        CREATE TABLE IF NOT EXISTS moderators (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Channel settings table
        await _execute("""
        CREATE TABLE IF NOT EXISTS channel_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            channel_link TEXT,
            discord_link TEXT,
            require_subscription BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tournaments table
        await _execute("""
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
        await _execute("""
        CREATE TABLE IF NOT EXISTS welcome_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tournament notifications table
        await _execute("""
        CREATE TABLE IF NOT EXISTS tournament_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            message TEXT,
            send_time TEXT,
            sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Superuser settings table
        await _execute("""
        CREATE TABLE IF NOT EXISTS superuser_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            password TEXT DEFAULT '1234',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Activity logs table
        await _execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Bot logs table
        await _execute("""
        CREATE TABLE IF NOT EXISTS bot_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT DEFAULT 'INFO',
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Registration settings table
        await _execute("""
        CREATE TABLE IF NOT EXISTS registration_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            require_epic BOOLEAN DEFAULT 1,
            require_discord BOOLEAN DEFAULT 1,
            require_rank BOOLEAN DEFAULT 1,
            require_peak_rank BOOLEAN DEFAULT 1,
            require_tracker BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Post-registration messages table
        await _execute("""
        CREATE TABLE IF NOT EXISTS post_registration_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Initialize default registration settings
        await _execute("""
        INSERT OR IGNORE INTO registration_settings (id, require_epic, require_discord, require_rank, require_peak_rank, require_tracker) 
        VALUES (1, 1, 1, 1, 1, 1)
        """)
        
        # Initialize superuser settings if not exists
        await _execute("""
        INSERT OR IGNORE INTO superuser_settings (id, password) VALUES (1, '1234')
        """)
        await _commit()
        
        print("✅ База данных инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        raise

# ── User Management ───────────────────────────────────────────────────────────────
async def add_user(tg_id, username="", epic="", discord="", rank="", peak_rank="", tracker=""):
    try:
        await _execute(
            "INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tg_id, username, epic, discord, rank, peak_rank, tracker)
        )
        await _commit()
        print(f"✅ Пользователь {tg_id} добавлен в БД")
        await log_activity(tg_id, username, "REGISTRATION", f"Epic: {epic}, Discord: {discord}")
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")

async def check_user(tg_id):
    try:
        cursor = await _execute("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,))
        row = await _fetchone(cursor)
        return row is not None
    except Exception as e:
        print(f"❌ Ошибка проверки пользователя: {e}")
        return False

async def get_user(tg_id):
    try:
        cursor = await _execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = await _fetchone(cursor)
        if row:
            columns = ["tg_id", "username", "epic", "discord", "rank", "peak_rank", "tracker"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return None

async def get_all_users():
    try:
        cursor = await _execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = await _fetchall(cursor)
        columns = ["tg_id", "username", "epic", "discord", "rank", "peak_rank", "tracker"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения всех пользователей: {e}")
        return []

async def delete_user(tg_id):
    try:
        await _execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        await _commit()
        print(f"✅ Пользователь {tg_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления пользователя: {e}")

async def update_user_field(tg_id, field, value):
    """Обновить конкретное поле пользователя"""
    valid_fields = ["epic", "discord", "rank", "peak_rank", "tracker"]
    if field not in valid_fields:
        print(f"❌ Неверное поле: {field}")
        return False
    try:
        await _execute(f"UPDATE users SET {field} = ? WHERE tg_id = ?", (value, tg_id))
        await _commit()
        print(f"✅ Поле {field} пользователя {tg_id} обновлено")
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления поля {field}: {e}")
        return False

async def delete_all_users():
    try:
        await _execute("DELETE FROM users")
        await _commit()
        print("✅ Все пользователи удалены из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления всех пользователей: {e}")

async def count_users():
    try:
        cursor = await _execute("SELECT COUNT(*) FROM users")
        count = await _fetchone(cursor)
        return count[0] if count else 0
    except Exception as e:
        print(f"❌ Ошибка подсчета пользователей: {e}")
        return 0

# ── Admin Management ───────────────────────────────────────────────────────────────
async def add_admin(tg_id, username="", added_by=0):
    try:
        await _execute(
            "INSERT OR REPLACE INTO admins (tg_id, username, added_by) VALUES (?, ?, ?)",
            (tg_id, username, added_by)
        )
        await _commit()
        print(f"✅ Админ {tg_id} добавлен в БД")
    except Exception as e:
        print(f"❌ Ошибка добавления админа: {e}")

async def remove_admin(tg_id):
    try:
        await _execute("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
        await _commit()
        print(f"✅ Админ {tg_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления админа: {e}")

async def get_all_admins():
    try:
        cursor = await _execute("SELECT * FROM admins ORDER BY added_at DESC")
        rows = await _fetchall(cursor)
        columns = ["tg_id", "username", "added_by", "added_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения админов: {e}")
        return []

async def is_admin_db(tg_id):
    try:
        cursor = await _execute("SELECT tg_id FROM admins WHERE tg_id = ?", (tg_id,))
        row = await _fetchone(cursor)
        return row is not None
    except Exception as e:
        print(f"❌ Ошибка проверки админа: {e}")
        return False

# ── Moderator Management ───────────────────────────────────────────────────────────
async def add_moderator(tg_id, username="", added_by=0):
    try:
        await _execute(
            "INSERT OR REPLACE INTO moderators (tg_id, username, added_by) VALUES (?, ?, ?)",
            (tg_id, username, added_by)
        )
        await _commit()
        print(f"✅ Модератор {tg_id} добавлен в БД")
    except Exception as e:
        print(f"❌ Ошибка добавления модератора: {e}")

async def remove_moderator(tg_id):
    try:
        await _execute("DELETE FROM moderators WHERE tg_id = ?", (tg_id,))
        await _commit()
        print(f"✅ Модератор {tg_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления модератора: {e}")

async def get_all_moderators():
    try:
        cursor = await _execute("SELECT * FROM moderators ORDER BY added_at DESC")
        rows = await _fetchall(cursor)
        columns = ["tg_id", "username", "added_by", "added_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения модераторов: {e}")
        return []

async def is_moderator(tg_id):
    try:
        cursor = await _execute("SELECT tg_id FROM moderators WHERE tg_id = ?", (tg_id,))
        row = await _fetchone(cursor)
        return row is not None
    except Exception as e:
        print(f"❌ Ошибка проверки модератора: {e}")
        return False

async def is_admin_or_moderator(tg_id):
    return await is_admin_db(tg_id) or await is_moderator(tg_id)

# ── Channel Settings ───────────────────────────────────────────────────────────────
async def update_channel_settings(channel_link="", discord_link="", require_subscription=False):
    try:
        await _execute(
            "INSERT OR REPLACE INTO channel_settings (id, channel_link, discord_link, require_subscription) VALUES (1, ?, ?, ?)",
            (channel_link, discord_link, require_subscription)
        )
        await _commit()
        print("✅ Настройки канала обновлены")
    except Exception as e:
        print(f"❌ Ошибка обновления настроек канала: {e}")

async def get_channel_settings():
    try:
        cursor = await _execute("SELECT * FROM channel_settings WHERE id = 1")
        row = await _fetchone(cursor)
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
        cursor = await _execute(
            "INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)",
            (name, description, date_time, max_players, prize)
        )
        tournament_id = cursor.lastrowid
        await _commit()
        print(f"✅ Турнир {tournament_id} добавлен в БД")
        return tournament_id
    except Exception as e:
        print(f"❌ Ошибка добавления турнира: {e}")
        return None

async def get_all_tournaments():
    try:
        cursor = await _execute("SELECT * FROM tournaments ORDER BY created_at DESC")
        rows = await _fetchall(cursor)
        columns = ["id", "name", "description", "date_time", "max_players", "prize", "created_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения турниров: {e}")
        return []

async def get_tournament(tournament_id):
    try:
        cursor = await _execute("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
        row = await _fetchone(cursor)
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
            await _execute(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", params)
            await _commit()
            print(f"✅ Турнир {tournament_id} обновлен")
    except Exception as e:
        print(f"❌ Ошибка обновления турнира: {e}")

async def delete_tournament(tournament_id):
    try:
        await _execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        await _commit()
        print(f"✅ Турнир {tournament_id} удален из БД")
    except Exception as e:
        print(f"❌ Ошибка удаления турнира: {e}")

# ── Welcome Message Management ───────────────────────────────────────────────────────
async def add_welcome_message(message):
    try:
        await _execute("UPDATE welcome_messages SET is_active = 0")
        
        cursor = await _execute(
            "INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)",
            (message,)
        )
        message_id = cursor.lastrowid
        await _commit()
        print(f"✅ Приветственное сообщение {message_id} добавлено")
        return message_id
    except Exception as e:
        print(f"❌ Ошибка добавления приветственного сообщения: {e}")
        return None

async def get_active_welcome_message():
    try:
        cursor = await _execute("SELECT * FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        row = await _fetchone(cursor)
        if row:
            columns = ["id", "message", "is_active", "created_at"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения активного приветственного сообщения: {e}")
        return None

async def update_welcome_message(message_id, message):
    try:
        await _execute(
            "UPDATE welcome_messages SET message = ? WHERE id = ?",
            (message, message_id)
        )
        await _commit()
        print(f"✅ Приветственное сообщение {message_id} обновлено")
    except Exception as e:
        print(f"❌ Ошибка обновления приветственного сообщения: {e}")

# ── Tournament Notifications Management ───────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    try:
        cursor = await _execute(
            "INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)",
            (tournament_id, message, send_time)
        )
        notification_id = cursor.lastrowid
        await _commit()
        print(f"✅ Уведомление {notification_id} добавлено")
        return notification_id
    except Exception as e:
        print(f"❌ Ошибка добавления уведомления: {e}")
        return None

async def get_pending_notifications():
    try:
        cursor = await _execute(
            "SELECT * FROM tournament_notifications WHERE sent = 0 ORDER BY send_time ASC"
        )
        rows = await _fetchall(cursor)
        columns = ["id", "tournament_id", "message", "send_time", "sent", "created_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения отложенных уведомлений: {e}")
        return []

async def mark_notification_sent(notification_id):
    try:
        await _execute(
            "UPDATE tournament_notifications SET sent = 1 WHERE id = ?",
            (notification_id,)
        )
        await _commit()
        print(f"✅ Уведомление {notification_id} отмечено как отправленное")
    except Exception as e:
        print(f"❌ Ошибка отметки уведомления как отправленного: {e}")

# ── SuperUser Settings ───────────────────────────────────────────────────────────────
async def get_superuser_password():
    try:
        cursor = await _execute("SELECT password FROM superuser_settings WHERE id = 1")
        row = await _fetchone(cursor)
        return row[0] if row else '1234'
    except Exception as e:
        print(f"❌ Ошибка получения пароля superuser: {e}")
        return '1234'

async def set_superuser_password(new_password):
    try:
        await _execute("UPDATE superuser_settings SET password = ? WHERE id = 1", (new_password,))
        await _commit()
        print("✅ Пароль superuser обновлён")
    except Exception as e:
        print(f"❌ Ошибка обновления пароля superuser: {e}")

# ── Activity Logging ───────────────────────────────────────────────────────────────
async def log_activity(user_id, username, action, details=""):
    try:
        await _execute(
            "INSERT INTO activity_logs (user_id, username, action, details) VALUES (?, ?, ?, ?)",
            (user_id, username, action, details)
        )
        await _commit()
    except Exception as e:
        print(f"❌ Ошибка логирования активности: {e}")

async def get_activity_logs(limit=50):
    try:
        cursor = await _execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await _fetchall(cursor)
        columns = ["id", "user_id", "username", "action", "details", "created_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения логов активности: {e}")
        return []

async def clear_activity_logs():
    try:
        await _execute("DELETE FROM activity_logs")
        await _commit()
        print("✅ Логи активности очищены")
    except Exception as e:
        print(f"❌ Ошибка очистки логов активности: {e}")

# ── Bot Logging ───────────────────────────────────────────────────────────────
async def log_bot(level, message):
    try:
        await _execute(
            "INSERT INTO bot_logs (level, message) VALUES (?, ?)",
            (level, message)
        )
        await _commit()
    except Exception as e:
        print(f"❌ Ошибка логирования бота: {e}")

async def get_bot_logs(limit=50):
    try:
        cursor = await _execute("SELECT * FROM bot_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = await _fetchall(cursor)
        columns = ["id", "level", "message", "created_at"]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка получения логов бота: {e}")
        return []

async def clear_bot_logs():
    try:
        await _execute("DELETE FROM bot_logs")
        await _commit()
        print("✅ Логи бота очищены")
    except Exception as e:
        print(f"❌ Ошибка очистки логов бота: {e}")

# ── Backup & Restore ───────────────────────────────────────────────────────────────
import json
from datetime import datetime

async def create_backup():
    """Создаёт бэкап всех данных в JSON"""
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "users": [],
        "admins": [],
        "moderators": [],
        "tournaments": [],
        "channel_settings": None,
        "welcome_messages": [],
        "superuser_settings": None,
    }
    
    try:
        # Users
        cursor = await _execute("SELECT * FROM users")
        columns = ["tg_id", "username", "epic", "discord", "rank", "peak_rank", "tracker", "created_at"]
        backup_data["users"] = [dict(zip(columns, row)) for row in await _fetchall(cursor)]
        
        # Admins
        cursor = await _execute("SELECT * FROM admins")
        columns = ["tg_id", "username", "added_by", "added_at"]
        backup_data["admins"] = [dict(zip(columns, row)) for row in await _fetchall(cursor)]
        
        # Moderators
        cursor = await _execute("SELECT * FROM moderators")
        columns = ["tg_id", "username", "added_by", "added_at"]
        backup_data["moderators"] = [dict(zip(columns, row)) for row in await _fetchall(cursor)]
        
        # Tournaments
        cursor = await _execute("SELECT * FROM tournaments")
        columns = ["id", "name", "description", "date_time", "max_players", "prize", "created_at"]
        backup_data["tournaments"] = [dict(zip(columns, row)) for row in await _fetchall(cursor)]
        
        # Channel settings
        cursor = await _execute("SELECT * FROM channel_settings WHERE id = 1")
        columns = ["id", "channel_link", "discord_link", "require_subscription", "created_at"]
        row = await _fetchone(cursor)
        if row:
            backup_data["channel_settings"] = dict(zip(columns, row))
        
        # Welcome messages
        cursor = await _execute("SELECT * FROM welcome_messages")
        columns = ["id", "message", "is_active", "created_at"]
        backup_data["welcome_messages"] = [dict(zip(columns, row)) for row in await _fetchall(cursor)]
        
        # Superuser settings
        cursor = await _execute("SELECT * FROM superuser_settings WHERE id = 1")
        columns = ["id", "password", "created_at"]
        row = await _fetchone(cursor)
        if row:
            backup_data["superuser_settings"] = dict(zip(columns, row))
        
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        await log_bot("BACKUP", f"Создан бэкап: {len(backup_data['users'])} пользователей, {len(backup_data['tournaments'])} турниров")
        
        return backup_json
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return None


async def restore_from_backup(backup_json):
    """Восстанавливает данные из JSON бэкапа"""
    try:
        data = json.loads(backup_json)
        
        # Clear existing data
        await _execute("DELETE FROM users")
        await _execute("DELETE FROM admins")
        await _execute("DELETE FROM moderators")
        await _execute("DELETE FROM tournaments")
        await _execute("DELETE FROM welcome_messages")
        await _commit()
        
        # Restore users
        for user in data.get("users", []):
            await _execute(
                "INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user["tg_id"], user["username"], user["epic"], user["discord"], user["rank"], user["peak_rank"], user.get("tracker", ""), user.get("created_at", ""))
            )
        
        # Restore admins
        for admin in data.get("admins", []):
            await _execute(
                "INSERT OR REPLACE INTO admins (tg_id, username, added_by, added_at) VALUES (?, ?, ?, ?)",
                (admin["tg_id"], admin["username"], admin["added_by"], admin["added_at"])
            )
        
        # Restore moderators
        for mod in data.get("moderators", []):
            await _execute(
                "INSERT OR REPLACE INTO moderators (tg_id, username, added_by, added_at) VALUES (?, ?, ?, ?)",
                (mod["tg_id"], mod["username"], mod["added_by"], mod["added_at"])
            )
        
        # Restore tournaments
        for tour in data.get("tournaments", []):
            await _execute(
                "INSERT INTO tournaments (id, name, description, date_time, max_players, prize, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tour["id"], tour["name"], tour["description"], tour["date_time"], tour["max_players"], tour["prize"], tour["created_at"])
            )
        
        # Restore welcome messages
        for wm in data.get("welcome_messages", []):
            await _execute(
                "INSERT INTO welcome_messages (id, message, is_active, created_at) VALUES (?, ?, ?, ?)",
                (wm["id"], wm["message"], wm["is_active"], wm["created_at"])
            )
        
        # Restore channel settings
        cs = data.get("channel_settings")
        if cs:
            await _execute(
                "INSERT OR REPLACE INTO channel_settings (id, channel_link, discord_link, require_subscription) VALUES (1, ?, ?, ?)",
                (cs["channel_link"], cs["discord_link"], cs["require_subscription"])
            )
        
        # Restore superuser settings
        su = data.get("superuser_settings")
        if su:
            await _execute(
                "INSERT OR REPLACE INTO superuser_settings (id, password) VALUES (1, ?)",
                (su["password"],)
            )
        
        await _commit()
        await log_bot("RESTORE", f"Восстановлено из бэкапа: {len(data.get('users', []))} пользователей")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка восстановления из бэкапа: {e}")
        return False


async def get_backup_count():
    """Получить количество записей для бэкапа"""
    try:
        users_cursor = await _execute("SELECT COUNT(*) FROM users")
        admins_cursor = await _execute("SELECT COUNT(*) FROM admins")
        tournaments_cursor = await _execute("SELECT COUNT(*) FROM tournaments")
        
        return {
            "users": (await _fetchone(users_cursor))[0],
            "admins": (await _fetchone(admins_cursor))[0],
            "tournaments": (await _fetchone(tournaments_cursor))[0],
        }
    except Exception as e:
        return {"users": 0, "admins": 0, "tournaments": 0}

# ── Registration Settings ───────────────────────────────────────────────────────────────
async def get_registration_settings():
    """Получить настройки регистрации"""
    try:
        cursor = await _execute("SELECT * FROM registration_settings WHERE id = 1")
        row = await _fetchone(cursor)
        if row:
            columns = ["id", "require_epic", "require_discord", "require_rank", "require_peak_rank", "require_tracker", "created_at"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения настроек регистрации: {e}")
        return None

async def update_registration_settings(**kwargs):
    """Обновить настройки регистрации"""
    try:
        settings = await get_registration_settings()
        if not settings:
            return False
        
        for key, value in kwargs.items():
            if key in settings:
                settings[key] = value
        
        await _execute(
            "UPDATE registration_settings SET require_epic = ?, require_discord = ?, require_rank = ?, require_peak_rank = ?, require_tracker = ? WHERE id = 1",
            (settings["require_epic"], settings["require_discord"], settings["require_rank"], settings["require_peak_rank"], settings["require_tracker"])
        )
        await _commit()
        print("✅ Настройки регистрации обновлены")
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления настроек регистрации: {e}")
        return False

# ── Post Registration Messages ───────────────────────────────────────────────────────────────
async def add_post_registration_message(message):
    """Добавить сообщение после регистрации"""
    try:
        await _execute("UPDATE post_registration_messages SET is_active = 0")
        cursor = await _execute(
            "INSERT INTO post_registration_messages (message, is_active) VALUES (?, 1)",
            (message,)
        )
        message_id = cursor.lastrowid
        await _commit()
        print(f"✅ Сообщение после регистрации {message_id} добавлено")
        return message_id
    except Exception as e:
        print(f"❌ Ошибка добавления сообщения после регистрации: {e}")
        return None

async def get_active_post_registration_message():
    """Получить активное сообщение после регистрации"""
    try:
        cursor = await _execute("SELECT * FROM post_registration_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        row = await _fetchone(cursor)
        if row:
            columns = ["id", "message", "is_active", "created_at"]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"❌ Ошибка получения сообщения после регистрации: {e}")
        return None

async def update_post_registration_message(message_id, message):
    """Обновить сообщение после регистрации"""
    try:
        await _execute(
            "UPDATE post_registration_messages SET message = ? WHERE id = ?",
            (message, message_id)
        )
        await _commit()
        print(f"✅ Сообщение после регистрации {message_id} обновлено")
    except Exception as e:
        print(f"❌ Ошибка обновления сообщения после регистрации: {e}")
