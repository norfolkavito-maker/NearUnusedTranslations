"""
Модуль работы с базой данных Turso.
Каждая операция создаёт отдельное подключение — никаких устаревших соединений.
"""
import asyncio
import json
import threading
from datetime import datetime
from config import TURSO_URL, TURSO_TOKEN

USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

# Глобальный lock для Turso подключений
_db_lock = threading.Lock()


def _get_conn():
    """Создаёт новое подключение к Turso"""
    if not USE_TURSO:
        raise RuntimeError("TURSO_URL/TURSO_TOKEN не настроен!")
    import libsql_experimental
    return libsql_experimental.connect(TURSO_URL, auth_token=TURSO_TOKEN)


def _fetchone(cursor):
    """Получить одну строку из курсора"""
    if cursor is None:
        return None
    try:
        return cursor.fetchone()
    except Exception:
        return None


def _fetchall(cursor):
    """Получить все строки из курсора"""
    if cursor is None:
        return []
    try:
        return cursor.fetchall()
    except Exception:
        return []


def _exec(sql, params=()):
    """Синхронное выполнение SQL с lock для потокобезопасности"""
    conn = _get_conn()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        print(f"   SQL: {sql}")
        if params:
            print(f"   Params: {params}")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def _safe_query(sql, params=()):
    """Безопасный запрос к БД с обработкой ошибок"""
    try:
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, lambda: _exec(sql, params))
        return cursor
    except Exception as e:
        print(f"❌ DB query error: {e}")
        return None


# ── Init DB ───────────────────────────────────────────────────────────────
def _init_db_sync():
    """Синхронная инициализация БД — вызывается напрямую до запуска бота"""
    conn = _get_conn()
    try:
        tables = [
            ("users", """CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY, username TEXT, epic TEXT,
                discord TEXT, rank TEXT, peak_rank TEXT, tracker TEXT,
                tournament_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("admins", """CREATE TABLE IF NOT EXISTS admins (
                tg_id INTEGER PRIMARY KEY, username TEXT,
                added_by INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("moderators", """CREATE TABLE IF NOT EXISTS moderators (
                tg_id INTEGER PRIMARY KEY, username TEXT,
                added_by INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("channel_settings", """CREATE TABLE IF NOT EXISTS channel_settings (
                id INTEGER PRIMARY KEY DEFAULT 1, channel_link TEXT,
                discord_link TEXT, require_subscription BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("tournaments", """CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                description TEXT, date_time TEXT, max_players INTEGER,
                prize TEXT, is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("welcome_messages", """CREATE TABLE IF NOT EXISTS welcome_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT,
                is_active BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("tournament_notifications", """CREATE TABLE IF NOT EXISTS tournament_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT, tournament_id INTEGER,
                message TEXT, send_time TEXT, sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("superuser_settings", """CREATE TABLE IF NOT EXISTS superuser_settings (
                id INTEGER PRIMARY KEY DEFAULT 1, password TEXT DEFAULT '1234',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("activity_logs", """CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                username TEXT, action TEXT, details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("bot_logs", """CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT DEFAULT 'INFO',
                message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("registration_settings", """CREATE TABLE IF NOT EXISTS registration_settings (
                id INTEGER PRIMARY KEY DEFAULT 1, require_epic BOOLEAN DEFAULT 1,
                require_discord BOOLEAN DEFAULT 1, require_rank BOOLEAN DEFAULT 1,
                require_peak_rank BOOLEAN DEFAULT 1, require_tracker BOOLEAN DEFAULT 1,
                registration_open BOOLEAN DEFAULT 1, require_tournament BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("post_registration_messages", """CREATE TABLE IF NOT EXISTS post_registration_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT,
                is_active BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
            ("user_messages", """CREATE TABLE IF NOT EXISTS user_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, from_tg_id INTEGER,
                from_username TEXT, message TEXT, is_read BOOLEAN DEFAULT 0,
                replied BOOLEAN DEFAULT 0, admin_reply TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
        ]
        for table_name, sql in tables:
            try:
                conn.execute(sql)
                conn.commit()
            except Exception as e:
                print(f"⚠️ Ошибка создания таблицы {table_name}: {e}")

        conn.execute("INSERT OR IGNORE INTO registration_settings (id, require_epic, require_discord, require_rank, require_peak_rank, require_tracker) VALUES (1, 1, 1, 1, 1, 1)")
        conn.execute("INSERT OR IGNORE INTO superuser_settings (id, password) VALUES (1, '1234')")
        conn.commit()
        print("✅ Все таблицы созданы в Turso")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def init_db():
    """Инициализация БД (async обёртка)"""
    if USE_TURSO:
        await asyncio.get_event_loop().run_in_executor(None, _init_db_sync)
        print("✅ База данных инициализирована (Turso)")
    else:
        print("⚠️ Turso не настроен — проверьте TURSO_URL и TURSO_TOKEN")


# ── User Management ───────────────────────────────────────────────────────
async def add_user(tg_id, username="", epic="", discord="", rank="", peak_rank="", tracker=""):
    try:
        await _safe_query(
            "INSERT OR REPLACE INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tg_id, username, epic, discord, rank, peak_rank, tracker))
        await log_activity(tg_id, username, "REGISTRATION", f"Epic: {epic}, Discord: {discord}")
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")


async def check_user(tg_id):
    try:
        cur = await _safe_query("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,))
        if cur is None:
            return False
        return _fetchone(cur) is not None
    except Exception:
        return False


async def get_user(tg_id):
    try:
        cur = await _safe_query("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        if cur is None:
            return None
        row = _fetchone(cur)
        if row:
            return dict(zip(["tg_id","username","epic","discord","rank","peak_rank","tracker","created_at"], row))
        return None
    except Exception:
        return None


async def get_all_users():
    try:
        cur = await _safe_query("SELECT * FROM users ORDER BY created_at DESC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["tg_id","username","epic","discord","rank","peak_rank","tracker","created_at"], r)) for r in rows]
    except Exception:
        return []


async def delete_user(tg_id):
    try:
        await _safe_query("DELETE FROM users WHERE tg_id = ?", (tg_id,))
    except Exception as e:
        print(f"❌ Ошибка удаления пользователя: {e}")


async def update_user_field(tg_id, field, value):
    if field not in ("epic","discord","rank","peak_rank","tracker"):
        return False
    try:
        await _safe_query(f"UPDATE users SET {field} = ? WHERE tg_id = ?", (value, tg_id))
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления пользователя: {e}")
        return False


async def count_users():
    try:
        cur = await _safe_query("SELECT COUNT(*) FROM users")
        if cur is None:
            return 0
        row = _fetchone(cur)
        return row[0] if row else 0
    except Exception:
        return 0


async def delete_all_users():
    try:
        await _safe_query("DELETE FROM users")
    except Exception as e:
        print(f"❌ Ошибка удаления всех пользователей: {e}")


# ── Admin Management ───────────────────────────────────────────────────────
async def add_admin(tg_id, username="", added_by=0):
    try:
        await _safe_query("INSERT OR REPLACE INTO admins (tg_id, username, added_by) VALUES (?, ?, ?)", (tg_id, username, added_by))
    except Exception as e:
        print(f"❌ Ошибка добавления админа: {e}")


async def remove_admin(tg_id):
    try:
        await _safe_query("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
    except Exception as e:
        print(f"❌ Ошибка удаления админа: {e}")


async def get_all_admins():
    try:
        cur = await _safe_query("SELECT * FROM admins ORDER BY added_at DESC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in rows]
    except Exception:
        return []


async def is_admin_db(tg_id):
    try:
        cur = await _safe_query("SELECT tg_id FROM admins WHERE tg_id = ?", (tg_id,))
        if cur is None:
            return False
        return _fetchone(cur) is not None
    except Exception:
        return False


# ── Moderator Management ─────────────────────────────────────────────────
async def add_moderator(tg_id, username="", added_by=0):
    try:
        await _safe_query("INSERT OR REPLACE INTO moderators (tg_id, username, added_by) VALUES (?, ?, ?)", (tg_id, username, added_by))
    except Exception as e:
        print(f"❌ Ошибка добавления модератора: {e}")


async def remove_moderator(tg_id):
    try:
        await _safe_query("DELETE FROM moderators WHERE tg_id = ?", (tg_id,))
    except Exception as e:
        print(f"❌ Ошибка удаления модератора: {e}")


async def get_all_moderators():
    try:
        cur = await _safe_query("SELECT * FROM moderators ORDER BY added_at DESC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in rows]
    except Exception:
        return []


async def is_moderator(tg_id):
    try:
        cur = await _safe_query("SELECT tg_id FROM moderators WHERE tg_id = ?", (tg_id,))
        if cur is None:
            return False
        return _fetchone(cur) is not None
    except Exception:
        return False


async def is_admin_or_moderator(tg_id):
    a = await is_admin_db(tg_id)
    m = await is_moderator(tg_id)
    return a or m


# ── Channel Settings ─────────────────────────────────────────────────────
async def update_channel_settings(channel_link=None, discord_link=None, require_subscription=None):
    """Обновляет только указанные поля, сохраняя остальные"""
    try:
        # Получаем текущие настройки
        current = await get_channel_settings()
        if not current:
            # Если настроек нет — создаём новые
            await _safe_query(
                "INSERT INTO channel_settings (id, channel_link, discord_link, require_subscription) VALUES (1, ?, ?, ?)",
                (channel_link or "", discord_link or "", require_subscription or False)
            )
            return
        
        # Обновляем только указанные поля
        new_channel = channel_link if channel_link is not None else current.get("channel_link", "")
        new_discord = discord_link if discord_link is not None else current.get("discord_link", "")
        new_require = require_subscription if require_subscription is not None else current.get("require_subscription", False)
        
        await _safe_query(
            "UPDATE channel_settings SET channel_link=?, discord_link=?, require_subscription=? WHERE id=1",
            (new_channel, new_discord, new_require)
        )
    except Exception as e:
        print(f"❌ Ошибка обновления настроек канала: {e}")


async def get_channel_settings():
    try:
        cur = await _safe_query("SELECT * FROM channel_settings WHERE id = 1")
        if cur is None:
            return None
        row = _fetchone(cur)
        if row:
            return dict(zip(["id","channel_link","discord_link","require_subscription","created_at"], row))
        return None
    except Exception:
        return None


# ── Tournament Management ────────────────────────────────────────────────
async def add_tournament(name, description="", date_time="", max_players=0, prize=""):
    try:
        cur = await _safe_query("INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)", (name, description, date_time, max_players, prize))
        if cur:
            return cur.lastrowid
        return None
    except Exception as e:
        print(f"❌ Ошибка добавления турнира: {e}")
        return None


async def get_all_tournaments():
    try:
        cur = await _safe_query("SELECT * FROM tournaments ORDER BY created_at DESC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","name","description","date_time","max_players","prize","created_at"], r)) for r in rows]
    except Exception:
        return []


async def get_tournament(tournament_id):
    try:
        cur = await _safe_query("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
        if cur is None:
            return None
        row = _fetchone(cur)
        if row:
            return dict(zip(["id","name","description","date_time","max_players","prize","created_at"], row))
        return None
    except Exception:
        return None


async def update_tournament(tournament_id, name=None, description=None, date_time=None, max_players=None, prize=None):
    try:
        updates, params = [], []
        if name is not None: updates.append("name = ?"); params.append(name)
        if description is not None: updates.append("description = ?"); params.append(description)
        if date_time is not None: updates.append("date_time = ?"); params.append(date_time)
        if max_players is not None: updates.append("max_players = ?"); params.append(max_players)
        if prize is not None: updates.append("prize = ?"); params.append(prize)
        if updates:
            params.append(tournament_id)
            await _safe_query(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", params)
    except Exception as e:
        print(f"❌ Ошибка обновления турнира: {e}")


async def delete_tournament(tournament_id):
    try:
        await _safe_query("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
    except Exception as e:
        print(f"❌ Ошибка удаления турнира: {e}")


# ── Welcome Messages ─────────────────────────────────────────────────────
async def add_welcome_message(message):
    try:
        await _safe_query("UPDATE welcome_messages SET is_active = 0")
        cur = await _safe_query("INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)", (message,))
        if cur:
            return cur.lastrowid
        return None
    except Exception as e:
        print(f"❌ Ошибка добавления приветствия: {e}")
        return None


async def get_active_welcome_message():
    try:
        cur = await _safe_query("SELECT * FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        if cur is None:
            return None
        row = _fetchone(cur)
        if row:
            return dict(zip(["id","message","is_active","created_at"], row))
        return None
    except Exception:
        return None


async def update_welcome_message(message_id, message):
    try:
        await _safe_query("UPDATE welcome_messages SET message = ? WHERE id = ?", (message, message_id))
    except Exception as e:
        print(f"❌ Ошибка обновления приветствия: {e}")


# ── Tournament Notifications ─────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    try:
        cur = await _safe_query("INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)", (tournament_id, message, send_time))
        if cur:
            return cur.lastrowid
        return None
    except Exception as e:
        print(f"❌ Ошибка добавления уведомления: {e}")
        return None


async def get_pending_notifications():
    try:
        cur = await _safe_query("SELECT * FROM tournament_notifications WHERE sent = 0 ORDER BY send_time ASC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","tournament_id","message","send_time","sent","created_at"], r)) for r in rows]
    except Exception:
        return []


async def mark_notification_sent(notification_id):
    try:
        await _safe_query("UPDATE tournament_notifications SET sent = 1 WHERE id = ?", (notification_id,))
    except Exception as e:
        print(f"❌ Ошибка отметки уведомления: {e}")


# ── SuperUser Settings ───────────────────────────────────────────────────
async def get_superuser_password():
    try:
        cur = await _safe_query("SELECT password FROM superuser_settings WHERE id = 1")
        if cur is None:
            return '1234'
        row = _fetchone(cur)
        return row[0] if row else '1234'
    except Exception:
        return '1234'


async def set_superuser_password(new_password):
    try:
        await _safe_query("UPDATE superuser_settings SET password = ? WHERE id = 1", (new_password,))
    except Exception as e:
        print(f"❌ Ошибка обновления пароля: {e}")


# ── Activity Logging ─────────────────────────────────────────────────────
async def log_activity(user_id, username, action, details=""):
    try:
        await _safe_query("INSERT INTO activity_logs (user_id, username, action, details) VALUES (?, ?, ?, ?)", (user_id, username, action, details))
    except Exception:
        pass


async def get_activity_logs(limit=50):
    try:
        cur = await _safe_query("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","user_id","username","action","details","created_at"], r)) for r in rows]
    except Exception:
        return []


async def clear_activity_logs():
    try:
        await _safe_query("DELETE FROM activity_logs")
    except Exception as e:
        print(f"❌ Ошибка очистки логов: {e}")


# ── Bot Logging ──────────────────────────────────────────────────────────
async def log_bot(level, message):
    try:
        await _safe_query("INSERT INTO bot_logs (level, message) VALUES (?, ?)", (level, message))
    except Exception:
        pass


async def get_bot_logs(limit=50):
    try:
        cur = await _safe_query("SELECT * FROM bot_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","level","message","created_at"], r)) for r in rows]
    except Exception:
        return []


async def clear_bot_logs():
    try:
        await _safe_query("DELETE FROM bot_logs")
    except Exception as e:
        print(f"❌ Ошибка очистки логов бота: {e}")


# ── Backup & Restore ─────────────────────────────────────────────────────
async def create_backup():
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "users": [], "admins": [], "moderators": [], "tournaments": [],
        "channel_settings": None, "welcome_messages": [], "superuser_settings": None,
    }
    try:
        cur = await _safe_query("SELECT * FROM users")
        if cur:
            backup_data["users"] = [dict(zip(["tg_id","username","epic","discord","rank","peak_rank","tracker","created_at"], r)) for r in _fetchall(cur)]
        cur = await _safe_query("SELECT * FROM admins")
        if cur:
            backup_data["admins"] = [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in _fetchall(cur)]
        cur = await _safe_query("SELECT * FROM moderators")
        if cur:
            backup_data["moderators"] = [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in _fetchall(cur)]
        cur = await _safe_query("SELECT * FROM tournaments")
        if cur:
            backup_data["tournaments"] = [dict(zip(["id","name","description","date_time","max_players","prize","created_at"], r)) for r in _fetchall(cur)]
        cur = await _safe_query("SELECT * FROM channel_settings WHERE id = 1")
        if cur:
            row = _fetchone(cur)
            if row:
                backup_data["channel_settings"] = dict(zip(["id","channel_link","discord_link","require_subscription","created_at"], row))
        cur = await _safe_query("SELECT * FROM welcome_messages")
        if cur:
            backup_data["welcome_messages"] = [dict(zip(["id","message","is_active","created_at"], r)) for r in _fetchall(cur)]
        cur = await _safe_query("SELECT * FROM superuser_settings WHERE id = 1")
        if cur:
            row = _fetchone(cur)
            if row:
                backup_data["superuser_settings"] = dict(zip(["id","password","created_at"], row))
        return json.dumps(backup_data, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return None


async def restore_from_backup(backup_json):
    try:
        data = json.loads(backup_json)
        await _safe_query("DELETE FROM users")
        await _safe_query("DELETE FROM admins")
        await _safe_query("DELETE FROM moderators")
        await _safe_query("DELETE FROM tournaments")
        await _safe_query("DELETE FROM welcome_messages")
        for u in data.get("users", []):
            await _safe_query("INSERT INTO users (tg_id,username,epic,discord,rank,peak_rank,tracker,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (u["tg_id"],u["username"],u["epic"],u["discord"],u["rank"],u["peak_rank"],u.get("tracker",""),u.get("created_at","")))
        for a in data.get("admins", []):
            await _safe_query("INSERT OR REPLACE INTO admins (tg_id,username,added_by,added_at) VALUES (?,?,?,?)",
                (a["tg_id"],a["username"],a["added_by"],a["added_at"]))
        for m in data.get("moderators", []):
            await _safe_query("INSERT OR REPLACE INTO moderators (tg_id,username,added_by,added_at) VALUES (?,?,?,?)",
                (m["tg_id"],m["username"],m["added_by"],m["added_at"]))
        for t in data.get("tournaments", []):
            await _safe_query("INSERT INTO tournaments (id,name,description,date_time,max_players,prize,created_at) VALUES (?,?,?,?,?,?,?)",
                (t["id"],t["name"],t["description"],t["date_time"],t["max_players"],t["prize"],t["created_at"]))
        for w in data.get("welcome_messages", []):
            await _safe_query("INSERT INTO welcome_messages (id,message,is_active,created_at) VALUES (?,?,?,?)",
                (w["id"],w["message"],w["is_active"],w["created_at"]))
        cs = data.get("channel_settings")
        if cs:
            await _safe_query("INSERT OR REPLACE INTO channel_settings (id,channel_link,discord_link,require_subscription) VALUES (1,?,?,?)",
                (cs["channel_link"],cs["discord_link"],cs["require_subscription"]))
        su = data.get("superuser_settings")
        if su:
            await _safe_query("INSERT OR REPLACE INTO superuser_settings (id,password) VALUES (1,?)", (su["password"],))
        return True
    except Exception as e:
        print(f"❌ Ошибка восстановления: {e}")
        return False


async def get_backup_count():
    try:
        cur_users = await _safe_query("SELECT COUNT(*) FROM users")
        cur_admins = await _safe_query("SELECT COUNT(*) FROM admins")
        cur_tournaments = await _safe_query("SELECT COUNT(*) FROM tournaments")
        u = _fetchone(cur_users)[0] if cur_users else 0
        a = _fetchone(cur_admins)[0] if cur_admins else 0
        t = _fetchone(cur_tournaments)[0] if cur_tournaments else 0
        return {"users": u, "admins": a, "tournaments": t}
    except Exception:
        return {"users": 0, "admins": 0, "tournaments": 0}


# ── Registration Settings ────────────────────────────────────────────────
async def get_registration_settings():
    try:
        cur = await _safe_query("SELECT * FROM registration_settings WHERE id = 1")
        if cur is None:
            return None
        row = _fetchone(cur)
        if row:
            return dict(zip(["id","require_epic","require_discord","require_rank","require_peak_rank","require_tracker","created_at"], row))
        return None
    except Exception:
        return None


async def update_registration_settings(**kwargs):
    settings = await get_registration_settings()
    if not settings:
        print(f"[DB] update_registration_settings: settings is None, returning False")
        return False
    for k, v in kwargs.items():
        if k in settings:
            settings[k] = v
    try:
        print(f"[DB] UPDATE registration_settings: {kwargs}")
        await _safe_query("UPDATE registration_settings SET require_epic=?,require_discord=?,require_rank=?,require_peak_rank=?,require_tracker=? WHERE id=1",
            (settings["require_epic"],settings["require_discord"],settings["require_rank"],settings["require_peak_rank"],settings["require_tracker"]))
        print(f"[DB] UPDATE successful")
        return True
    except Exception as e:
        print(f"[DB] UPDATE error: {e}")
        return False


# ── Post Registration Messages ───────────────────────────────────────────
async def add_post_registration_message(message):
    try:
        await _safe_query("UPDATE post_registration_messages SET is_active = 0")
        cur = await _safe_query("INSERT INTO post_registration_messages (message, is_active) VALUES (?, 1)", (message,))
        if cur:
            return cur.lastrowid
        return None
    except Exception as e:
        print(f"❌ Ошибка добавления сообщения: {e}")
        return None


async def get_active_post_registration_message():
    try:
        cur = await _safe_query("SELECT * FROM post_registration_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        if cur is None:
            return None
        row = _fetchone(cur)
        if row:
            return dict(zip(["id","message","is_active","created_at"], row))
        return None
    except Exception:
        return None


async def update_post_registration_message(message_id, message):
    try:
        await _safe_query("UPDATE post_registration_messages SET message = ? WHERE id = ?", (message, message_id))
    except Exception as e:
        print(f"❌ Ошибка обновления сообщения: {e}")


# ── User Messages (Contact Admins) ───────────────────────────────────────────
async def add_user_message(from_tg_id, from_username, message):
    """Сохранить новое сообщение от пользователя"""
    try:
        cur = await _safe_query(
            "INSERT INTO user_messages (from_tg_id, from_username, message) VALUES (?, ?, ?)",
            (from_tg_id, from_username, message)
        )
        if cur:
            return cur.lastrowid
        return None
    except Exception as e:
        print(f"❌ Ошибка сохранения сообщения: {e}")
        return None


async def get_unread_messages():
    """Получить непрочитанные сообщения"""
    try:
        cur = await _safe_query("SELECT * FROM user_messages WHERE is_read = 0 ORDER BY created_at DESC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","from_tg_id","from_username","message","is_read","replied","admin_reply","created_at"], r)) for r in rows]
    except Exception:
        return []


async def get_all_messages(limit=50):
    """Получить все сообщения"""
    try:
        cur = await _safe_query("SELECT * FROM user_messages ORDER BY created_at DESC LIMIT ?", (limit,))
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","from_tg_id","from_username","message","is_read","replied","admin_reply","created_at"], r)) for r in rows]
    except Exception:
        return []


async def mark_message_read(msg_id):
    """Отметить сообщение как прочитанное"""
    try:
        await _safe_query("UPDATE user_messages SET is_read = 1 WHERE id = ?", (msg_id,))
    except Exception as e:
        print(f"❌ Ошибка отметки сообщения: {e}")


async def mark_message_replied(msg_id, admin_reply):
    """Отметить сообщение как отвеченное"""
    try:
        await _safe_query("UPDATE user_messages SET replied = 1, admin_reply = ? WHERE id = ?", (admin_reply, msg_id))
    except Exception as e:
        print(f"❌ Ошибка обновления ответа: {e}")


async def get_unread_messages_count():
    """Получить количество непрочитанных сообщений"""
    try:
        cur = await _safe_query("SELECT COUNT(*) FROM user_messages WHERE is_read = 0")
        if cur is None:
            return 0
        row = _fetchone(cur)
        return row[0] if row else 0
    except Exception:
        return 0


# ── Duplicate Detection ──────────────────────────────────────────────────────
async def find_duplicate_usernames():
    """Найти дубликаты по username (без учёта @)"""
    try:
        cur = await _safe_query("""
            SELECT LOWER(REPLACE(username, '@', '')) as clean_username, COUNT(*) as cnt,
                   GROUP_CONCAT(tg_id) as ids, GROUP_CONCAT(username) as usernames
            FROM users 
            WHERE username IS NOT NULL AND username != '' 
            GROUP BY LOWER(REPLACE(username, '@', ''))
            HAVING cnt > 1
            ORDER BY cnt DESC
        """)
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["clean_username","cnt","ids","usernames"], r)) for r in rows]
    except Exception as e:
        print(f"❌ Ошибка поиска дубликатов: {e}")
        return []


async def delete_user_by_tg_id(tg_id):
    """Удалить конкретного пользователя по ID"""
    try:
        # Сначала получаем данные пользователя для уведомления
        user = await get_user(tg_id)
        await _safe_query("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        return user
    except Exception as e:
        print(f"❌ Ошибка удаления пользователя: {e}")
        return None


# ── Tournament Registration Control ──────────────────────────────────────────
async def is_registration_open():
    """Проверить открыта ли регистрация"""
    try:
        cur = await _safe_query("SELECT registration_open FROM registration_settings WHERE id = 1")
        if cur is None:
            return True
        row = _fetchone(cur)
        if row:
            return bool(row[0])
        return True
    except Exception:
        return True


async def toggle_registration():
    """Переключить статус регистрации (открыта/закрыта)"""
    try:
        current = await is_registration_open()
        new_status = not current
        await _safe_query("UPDATE registration_settings SET registration_open = ? WHERE id = 1", (new_status,))
        return new_status
    except Exception as e:
        print(f"❌ Ошибка переключения регистрации: {e}")
        return None


async def get_active_tournaments():
    """Получить активные турниры"""
    try:
        cur = await _safe_query("SELECT * FROM tournaments WHERE is_active = 1 ORDER BY date_time ASC")
        if cur is None:
            return []
        rows = _fetchall(cur)
        return [dict(zip(["id","name","description","date_time","max_players","prize","is_active","created_at"], r)) for r in rows]
    except Exception:
        return []


async def update_user_tournament(tg_id, tournament_id):
    """Обновить турнир пользователя"""
    try:
        await _safe_query("UPDATE users SET tournament_id = ? WHERE tg_id = ?", (tournament_id, tg_id))
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления турнира пользователя: {e}")
        return False


async def get_user_tournament(tg_id):
    """Получить турнир пользователя"""
    try:
        cur = await _safe_query("SELECT tournament_id FROM users WHERE tg_id = ?", (tg_id,))
        if cur is None:
            return None
        row = _fetchone(cur)
        return row[0] if row else None
    except Exception:
        return None
