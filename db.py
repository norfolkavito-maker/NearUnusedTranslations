"""
Модуль работы с базой данных Turso.
Каждая операция создаёт отдельное подключение — никаких устаревших соединений.
"""
import asyncio
import json
from datetime import datetime
from config import TURSO_URL, TURSO_TOKEN

USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)


def _get_conn():
    """Создаёт новое подключение к Turso"""
    import libsql_experimental
    return libsql_experimental.connect(TURSO_URL, auth_token=TURSO_TOKEN)


def _exec(sql, params=()):
    """Синхронное выполнение SQL"""
    conn = _get_conn()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


async def _run(func, *args):
    """Запуск синхронной функции в thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args) if args else func())


async def init_db():
    """Создать все таблицы"""
    def _init():
        conn = _get_conn()
        try:
            tables = [
                """CREATE TABLE IF NOT EXISTS users (
                    tg_id INTEGER PRIMARY KEY, username TEXT, epic TEXT,
                    discord TEXT, rank TEXT, peak_rank TEXT, tracker TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS admins (
                    tg_id INTEGER PRIMARY KEY, username TEXT,
                    added_by INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS moderators (
                    tg_id INTEGER PRIMARY KEY, username TEXT,
                    added_by INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS channel_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1, channel_link TEXT,
                    discord_link TEXT, require_subscription BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                    description TEXT, date_time TEXT, max_players INTEGER,
                    prize TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS welcome_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT,
                    is_active BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS tournament_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tournament_id INTEGER,
                    message TEXT, send_time TEXT, sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS superuser_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1, password TEXT DEFAULT '1234',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    username TEXT, action TEXT, details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS bot_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT DEFAULT 'INFO',
                    message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS registration_settings (
                    id INTEGER PRIMARY KEY DEFAULT 1, require_epic BOOLEAN DEFAULT 1,
                    require_discord BOOLEAN DEFAULT 1, require_rank BOOLEAN DEFAULT 1,
                    require_peak_rank BOOLEAN DEFAULT 1, require_tracker BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
                """CREATE TABLE IF NOT EXISTS post_registration_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT,
                    is_active BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
            ]
            for sql in tables:
                conn.execute(sql)
            conn.execute("INSERT OR IGNORE INTO registration_settings (id, require_epic, require_discord, require_rank, require_peak_rank, require_tracker) VALUES (1, 1, 1, 1, 1, 1)")
            conn.execute("INSERT OR IGNORE INTO superuser_settings (id, password) VALUES (1, '1234')")
            conn.commit()
            print(f"✅ Все таблицы созданы в Turso")
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            raise
        finally:
            conn.close()

    try:
        await _run(_init)
        print(f"✅ База данных инициализирована (Turso: {USE_TURSO})")
    except Exception as e:
        print(f"❌ Критическая ошибка init_db: {e}")
        import traceback
        traceback.print_exc()
        raise


# ── User Management ───────────────────────────────────────────────────────────────
async def add_user(tg_id, username="", epic="", discord="", rank="", peak_rank="", tracker=""):
    def _add():
        _exec("INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (tg_id, username, epic, discord, rank, peak_rank, tracker))
    await _run(_add)
    await log_activity(tg_id, username, "REGISTRATION", f"Epic: {epic}, Discord: {discord}")


async def check_user(tg_id):
    def _check():
        cur = _exec("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,))
        return cur.fetchone() is not None
    return await _run(_check)


async def get_user(tg_id):
    def _get():
        cur = _exec("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = cur.fetchone()
        if row:
            return dict(zip(["tg_id","username","epic","discord","rank","peak_rank","tracker","created_at"], row))
        return None
    return await _run(_get)


async def get_all_users():
    def _get_all():
        cur = _exec("SELECT * FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(zip(["tg_id","username","epic","discord","rank","peak_rank","tracker","created_at"], r)) for r in rows]
    return await _run(_get_all)


async def delete_user(tg_id):
    await _run(lambda: _exec("DELETE FROM users WHERE tg_id = ?", (tg_id,)))


async def update_user_field(tg_id, field, value):
    if field not in ("epic","discord","rank","peak_rank","tracker"):
        return False
    await _run(lambda: _exec(f"UPDATE users SET {field} = ? WHERE tg_id = ?", (value, tg_id)))
    return True


async def delete_all_users():
    await _run(lambda: _exec("DELETE FROM users"))


async def count_users():
    def _count():
        cur = _exec("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]
    return await _run(_count)


# ── Admin Management ───────────────────────────────────────────────────────────────
async def add_admin(tg_id, username="", added_by=0):
    await _run(lambda: _exec("INSERT OR REPLACE INTO admins (tg_id, username, added_by) VALUES (?, ?, ?)", (tg_id, username, added_by)))


async def remove_admin(tg_id):
    await _run(lambda: _exec("DELETE FROM admins WHERE tg_id = ?", (tg_id,)))


async def get_all_admins():
    def _get():
        cur = _exec("SELECT * FROM admins ORDER BY added_at DESC")
        return [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in cur.fetchall()]
    return await _run(_get)


async def is_admin_db(tg_id):
    return await _run(lambda: _exec("SELECT tg_id FROM admins WHERE tg_id = ?", (tg_id,)).fetchone() is not None)


# ── Moderator Management ───────────────────────────────────────────────────────────
async def add_moderator(tg_id, username="", added_by=0):
    await _run(lambda: _exec("INSERT OR REPLACE INTO moderators (tg_id, username, added_by) VALUES (?, ?, ?)", (tg_id, username, added_by)))


async def remove_moderator(tg_id):
    await _run(lambda: _exec("DELETE FROM moderators WHERE tg_id = ?", (tg_id,)))


async def get_all_moderators():
    def _get():
        cur = _exec("SELECT * FROM moderators ORDER BY added_at DESC")
        return [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in cur.fetchall()]
    return await _run(_get)


async def is_moderator(tg_id):
    return await _run(lambda: _exec("SELECT tg_id FROM moderators WHERE tg_id = ?", (tg_id,)).fetchone() is not None)


async def is_admin_or_moderator(tg_id):
    a = await is_admin_db(tg_id)
    m = await is_moderator(tg_id)
    return a or m


# ── Channel Settings ───────────────────────────────────────────────────────────────
async def update_channel_settings(channel_link="", discord_link="", require_subscription=False):
    await _run(lambda: _exec("INSERT OR REPLACE INTO channel_settings (id, channel_link, discord_link, require_subscription) VALUES (1, ?, ?, ?)", (channel_link, discord_link, require_subscription)))


async def get_channel_settings():
    def _get():
        cur = _exec("SELECT * FROM channel_settings WHERE id = 1")
        row = cur.fetchone()
        if row:
            return dict(zip(["id","channel_link","discord_link","require_subscription","created_at"], row))
        return None
    return await _run(_get)


# ── Tournament Management ───────────────────────────────────────────────────────────
async def add_tournament(name, description="", date_time="", max_players=0, prize=""):
    def _add():
        cur = _exec("INSERT INTO tournaments (name, description, date_time, max_players, prize) VALUES (?, ?, ?, ?, ?)", (name, description, date_time, max_players, prize))
        return cur.lastrowid
    return await _run(_add)


async def get_all_tournaments():
    def _get():
        cur = _exec("SELECT * FROM tournaments ORDER BY created_at DESC")
        return [dict(zip(["id","name","description","date_time","max_players","prize","created_at"], r)) for r in cur.fetchall()]
    return await _run(_get)


async def get_tournament(tournament_id):
    def _get():
        cur = _exec("SELECT * FROM tournaments WHERE id = ?", (tournament_id,))
        row = cur.fetchone()
        if row:
            return dict(zip(["id","name","description","date_time","max_players","prize","created_at"], row))
        return None
    return await _run(_get)


async def update_tournament(tournament_id, name=None, description=None, date_time=None, max_players=None, prize=None):
    def _upd():
        updates, params = [], []
        if name is not None: updates.append("name = ?"); params.append(name)
        if description is not None: updates.append("description = ?"); params.append(description)
        if date_time is not None: updates.append("date_time = ?"); params.append(date_time)
        if max_players is not None: updates.append("max_players = ?"); params.append(max_players)
        if prize is not None: updates.append("prize = ?"); params.append(prize)
        if updates:
            params.append(tournament_id)
            _exec(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", params)
    await _run(_upd)


async def delete_tournament(tournament_id):
    await _run(lambda: _exec("DELETE FROM tournaments WHERE id = ?", (tournament_id,)))


# ── Welcome Messages ───────────────────────────────────────────────────────────────
async def add_welcome_message(message):
    def _add():
        _exec("UPDATE welcome_messages SET is_active = 0")
        cur = _exec("INSERT INTO welcome_messages (message, is_active) VALUES (?, 1)", (message,))
        return cur.lastrowid
    return await _run(_add)


async def get_active_welcome_message():
    def _get():
        cur = _exec("SELECT * FROM welcome_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return dict(zip(["id","message","is_active","created_at"], row))
        return None
    return await _run(_get)


async def update_welcome_message(message_id, message):
    await _run(lambda: _exec("UPDATE welcome_messages SET message = ? WHERE id = ?", (message, message_id)))


# ── Tournament Notifications ───────────────────────────────────────────────────────
async def add_tournament_notification(tournament_id, message, send_time):
    def _add():
        cur = _exec("INSERT INTO tournament_notifications (tournament_id, message, send_time) VALUES (?, ?, ?)", (tournament_id, message, send_time))
        return cur.lastrowid
    return await _run(_add)


async def get_pending_notifications():
    def _get():
        cur = _exec("SELECT * FROM tournament_notifications WHERE sent = 0 ORDER BY send_time ASC")
        return [dict(zip(["id","tournament_id","message","send_time","sent","created_at"], r)) for r in cur.fetchall()]
    return await _run(_get)


async def mark_notification_sent(notification_id):
    await _run(lambda: _exec("UPDATE tournament_notifications SET sent = 1 WHERE id = ?", (notification_id,)))


# ── SuperUser Settings ───────────────────────────────────────────────────────────────
async def get_superuser_password():
    def _get():
        cur = _exec("SELECT password FROM superuser_settings WHERE id = 1")
        row = cur.fetchone()
        return row[0] if row else '1234'
    return await _run(_get)


async def set_superuser_password(new_password):
    await _run(lambda: _exec("UPDATE superuser_settings SET password = ? WHERE id = 1", (new_password,)))


# ── Activity Logging ───────────────────────────────────────────────────────────────
async def log_activity(user_id, username, action, details=""):
    try:
        await _run(lambda: _exec("INSERT INTO activity_logs (user_id, username, action, details) VALUES (?, ?, ?, ?)", (user_id, username, action, details)))
    except Exception:
        pass


async def get_activity_logs(limit=50):
    def _get():
        cur = _exec("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(zip(["id","user_id","username","action","details","created_at"], r)) for r in cur.fetchall()]
    return await _run(_get)


async def clear_activity_logs():
    await _run(lambda: _exec("DELETE FROM activity_logs"))


# ── Bot Logging ───────────────────────────────────────────────────────────────
async def log_bot(level, message):
    try:
        await _run(lambda: _exec("INSERT INTO bot_logs (level, message) VALUES (?, ?)", (level, message)))
    except Exception:
        pass


async def get_bot_logs(limit=50):
    def _get():
        cur = _exec("SELECT * FROM bot_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(zip(["id","level","message","created_at"], r)) for r in cur.fetchall()]
    return await _run(_get)


async def clear_bot_logs():
    await _run(lambda: _exec("DELETE FROM bot_logs"))


# ── Backup & Restore ───────────────────────────────────────────────────────────────
async def create_backup():
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "users": [], "admins": [], "moderators": [], "tournaments": [],
        "channel_settings": None, "welcome_messages": [], "superuser_settings": None,
    }
    try:
        def _backup():
            cur = _exec("SELECT * FROM users")
            backup_data["users"] = [dict(zip(["tg_id","username","epic","discord","rank","peak_rank","tracker","created_at"], r)) for r in cur.fetchall()]
            cur = _exec("SELECT * FROM admins")
            backup_data["admins"] = [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in cur.fetchall()]
            cur = _exec("SELECT * FROM moderators")
            backup_data["moderators"] = [dict(zip(["tg_id","username","added_by","added_at"], r)) for r in cur.fetchall()]
            cur = _exec("SELECT * FROM tournaments")
            backup_data["tournaments"] = [dict(zip(["id","name","description","date_time","max_players","prize","created_at"], r)) for r in cur.fetchall()]
            cur = _exec("SELECT * FROM channel_settings WHERE id = 1")
            row = cur.fetchone()
            if row:
                backup_data["channel_settings"] = dict(zip(["id","channel_link","discord_link","require_subscription","created_at"], row))
            cur = _exec("SELECT * FROM welcome_messages")
            backup_data["welcome_messages"] = [dict(zip(["id","message","is_active","created_at"], r)) for r in cur.fetchall()]
            cur = _exec("SELECT * FROM superuser_settings WHERE id = 1")
            row = cur.fetchone()
            if row:
                backup_data["superuser_settings"] = dict(zip(["id","password","created_at"], row))
        await _run(_backup)
        return json.dumps(backup_data, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return None


async def restore_from_backup(backup_json):
    try:
        data = json.loads(backup_json)
        def _restore():
            _exec("DELETE FROM users"); _exec("DELETE FROM admins"); _exec("DELETE FROM moderators")
            _exec("DELETE FROM tournaments"); _exec("DELETE FROM welcome_messages")
            for u in data.get("users", []):
                _exec("INSERT INTO users (tg_id,username,epic,discord,rank,peak_rank,tracker,created_at) VALUES (?,?,?,?,?,?,?,?)",
                      (u["tg_id"],u["username"],u["epic"],u["discord"],u["rank"],u["peak_rank"],u.get("tracker",""),u.get("created_at","")))
            for a in data.get("admins", []):
                _exec("INSERT OR REPLACE INTO admins (tg_id,username,added_by,added_at) VALUES (?,?,?,?)",
                      (a["tg_id"],a["username"],a["added_by"],a["added_at"]))
            for m in data.get("moderators", []):
                _exec("INSERT OR REPLACE INTO moderators (tg_id,username,added_by,added_at) VALUES (?,?,?,?)",
                      (m["tg_id"],m["username"],m["added_by"],m["added_at"]))
            for t in data.get("tournaments", []):
                _exec("INSERT INTO tournaments (id,name,description,date_time,max_players,prize,created_at) VALUES (?,?,?,?,?,?,?)",
                      (t["id"],t["name"],t["description"],t["date_time"],t["max_players"],t["prize"],t["created_at"]))
            for w in data.get("welcome_messages", []):
                _exec("INSERT INTO welcome_messages (id,message,is_active,created_at) VALUES (?,?,?,?)",
                      (w["id"],w["message"],w["is_active"],w["created_at"]))
            cs = data.get("channel_settings")
            if cs:
                _exec("INSERT OR REPLACE INTO channel_settings (id,channel_link,discord_link,require_subscription) VALUES (1,?,?,?)",
                      (cs["channel_link"],cs["discord_link"],cs["require_subscription"]))
            su = data.get("superuser_settings")
            if su:
                _exec("INSERT OR REPLACE INTO superuser_settings (id,password) VALUES (1,?)", (su["password"],))
        await _run(_restore)
        return True
    except Exception as e:
        print(f"❌ Ошибка восстановления: {e}")
        return False


async def get_backup_count():
    def _count():
        u = _exec("SELECT COUNT(*) FROM users").fetchone()[0]
        a = _exec("SELECT COUNT(*) FROM admins").fetchone()[0]
        t = _exec("SELECT COUNT(*) FROM tournaments").fetchone()[0]
        return {"users": u, "admins": a, "tournaments": t}
    return await _run(_count)


# ── Registration Settings ───────────────────────────────────────────────────────────────
async def get_registration_settings():
    def _get():
        cur = _exec("SELECT * FROM registration_settings WHERE id = 1")
        row = cur.fetchone()
        if row:
            return dict(zip(["id","require_epic","require_discord","require_rank","require_peak_rank","require_tracker","created_at"], row))
        return None
    return await _run(_get)


async def update_registration_settings(**kwargs):
    settings = await get_registration_settings()
    if not settings:
        return False
    for k, v in kwargs.items():
        if k in settings:
            settings[k] = v
    def _upd():
        _exec("UPDATE registration_settings SET require_epic=?,require_discord=?,require_rank=?,require_peak_rank=?,require_tracker=? WHERE id=1",
              (settings["require_epic"],settings["require_discord"],settings["require_rank"],settings["require_peak_rank"],settings["require_tracker"]))
    await _run(_upd)
    return True


# ── Post Registration Messages ───────────────────────────────────────────────────────────────
async def add_post_registration_message(message):
    def _add():
        _exec("UPDATE post_registration_messages SET is_active = 0")
        cur = _exec("INSERT INTO post_registration_messages (message, is_active) VALUES (?, 1)", (message,))
        return cur.lastrowid
    return await _run(_add)


async def get_active_post_registration_message():
    def _get():
        cur = _exec("SELECT * FROM post_registration_messages WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return dict(zip(["id","message","is_active","created_at"], row))
        return None
    return await _run(_get)


async def update_post_registration_message(message_id, message):
    await _run(lambda: _exec("UPDATE post_registration_messages SET message = ? WHERE id = ?", (message, message_id)))