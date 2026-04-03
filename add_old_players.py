"""Script to add old players to the database"""
import asyncio
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override config env vars to disable Turso locally
os.environ["TURSO_URL"] = ""
os.environ["TURSO_TOKEN"] = ""

import aiosqlite

OLD_PLAYERS = [
    {"tg_id": 820870350, "username": "valiauh", "epic": "de7cce031eb04b0db7d2c8922738bbc7", "discord": "valiauh", "rank": "Чемпион 2 / Дивизион 3 (1248 MMR)", "peak_rank": "ГЧ1 (1537 MMR)", "tracker": ""},
    {"tg_id": 853216552, "username": "Cylics", "epic": "fe5a998215454a77b493d074e2c5234a", "discord": "pupupu67", "rank": "Чемпион 2 / Дивизион 2 (1215 MMR)", "peak_rank": "ГЧ1 (1435 MMR)", "tracker": ""},
    {"tg_id": 892953049, "username": "qwelyx", "epic": "Qwelyx.", "discord": "Walak.", "rank": "Чемпион 3 / Дивизион 1 (1315 MMR)", "peak_rank": "ГЧ1 (1435 MMR)", "tracker": ""},
    {"tg_id": 984566385, "username": "xzdaqwd", "epic": "g0tthejuice", "discord": "1006872", "rank": "Чемпион 1 / Дивизион 4 (1162 MMR)", "peak_rank": "Чемпион 2 / Дивизион 4 (1282 MMR)", "tracker": ""},
    {"tg_id": 1027866429, "username": "almuted", "epic": "Schmurdya", "discord": "schmurdya", "rank": "MMR: 1070", "peak_rank": "Чемпион 3 / Дивизион 2 (1335 MMR)", "tracker": ""},
    {"tg_id": 1455661269, "username": "CheSlychilos", "epic": "ForgetMyName_", "discord": "piredozzza", "rank": "Чемпион 1 / Дивизион 4 (1162 MMR)", "peak_rank": "Чемпион 3 / Дивизион 3 (1372 MMR)", "tracker": ""},
    {"tg_id": 1696948772, "username": "furrynigger69", "epic": "Lev1k40", "discord": "levandosik_kakosik", "rank": "Чемпион 3 / Дивизион 1 (1315 MMR)", "peak_rank": "Чемпион 3 / Дивизион 4 (1402 MMR)", "tracker": ""},
    {"tg_id": 2097749803, "username": "Korrya76", "epic": "KORRYA_mc", "discord": "Korrya76", "rank": "Даймонд 1 / Дивизион 3 (873 MMR)", "peak_rank": "Чемпион 1 / Дивизион 2 (1095 MMR)", "tracker": ""},
    {"tg_id": 5208295687, "username": "M1rpe", "epic": "4f78a67a7f444bf19f82f7acc309c093", "discord": "okeokeoka", "rank": "Чемпион 2 / Дивизион 3 (1248 MMR)", "peak_rank": "Чемпион 3 / Дивизион 1 (1315 MMR)", "tracker": ""},
    {"tg_id": 5315781827, "username": "dinilama", "epic": "Бля(", "discord": "mvnicx", "rank": "Чемпион 1 / Дивизион 1 (1075 MMR)", "peak_rank": "Чемпион 1 / Дивизион 3 (1128 MMR)", "tracker": ""},
    {"tg_id": 5975741277, "username": "ribmus", "epic": "Buchptz", "discord": "ribmus", "rank": "Даймонд 3 / Дивизион 1 (995 MMR)", "peak_rank": "Чемпион 1 / Дивизион 1 (1075 MMR)", "tracker": ""},
    {"tg_id": 6424764691, "username": "Саня", "epic": "w1nbl", "discord": "w1nbl_", "rank": "Чемпион 2 / Дивизион 1 (1195 MMR)", "peak_rank": "Чемпион 2 / Дивизион 1 (1195 MMR)", "tracker": ""},
    {"tg_id": 8420004944, "username": "Popolovnik", "epic": "DSoymon4ik", "discord": "dsoymon4ik.", "rank": "Даймонд 3 / Дивизион 4 (1052 MMR)", "peak_rank": "Чемпион 1 / Дивизион 1 (1075 MMR)", "tracker": ""},
]

DB_PATH = "./users.db"

async def main():
    print(f"🗄️ Подключение к локальной БД: {DB_PATH}")
    
    async with aiosqlite.connect(DB_PATH) as conn:
        # Create table if not exists (same schema as db.py)
        await conn.execute("""
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
        await conn.commit()
        
        added = 0
        skipped = 0
        updated = 0
        
        for player in OLD_PLAYERS:
            # Check if user exists
            cursor = await conn.execute("SELECT tg_id FROM users WHERE tg_id = ?", (player["tg_id"],))
            row = await cursor.fetchone()
            
            if row:
                # Update existing player
                await conn.execute("""
                    UPDATE users SET 
                        username = ?, epic = ?, discord = ?, 
                        rank = ?, peak_rank = ?, tracker = ?
                    WHERE tg_id = ?
                """, (
                    player["username"], player["epic"], player["discord"],
                    player["rank"], player["peak_rank"], player["tracker"],
                    player["tg_id"]
                ))
                print(f"🔄 @{player['username']} обновлен")
                updated += 1
            else:
                # Insert new player
                await conn.execute("""
                    INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    player["tg_id"], player["username"], player["epic"], player["discord"],
                    player["rank"], player["peak_rank"], player["tracker"]
                ))
                print(f"✅ @{player['username']} добавлен")
                added += 1
        
        await conn.commit()
        
        # Show all players in DB
        print("\n📋 Все игроки в базе:")
        cursor = await conn.execute("SELECT tg_id, username, epic FROM users ORDER BY username")
        rows = await cursor.fetchall()
        for tg_id, username, epic in rows:
            print(f"   @{username} | {tg_id} | Epic: {epic}")
        
        print(f"\n✅ Готово! Добавлено: {added}, Обновлено: {updated}, Пропущено: {skipped}")
        print(f"📁 База данных: {DB_PATH}")

if __name__ == "__main__":
    asyncio.run(main())