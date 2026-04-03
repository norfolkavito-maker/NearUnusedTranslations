#!/usr/bin/env python3
"""
Скрипт импорта 8 игроков напрямую в Turso БД.
Игроки будут видны в админ-панели, учитываться в количестве, получать рассылки.

Запуск на Railway Shell:
    python import_players.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TURSO_URL, TURSO_TOKEN

PLAYERS = [
    (820870350, "valiauh", "de7cce031eb04b0db7d2c8922738bbc7", "valiauh", "Чемпион 2 / Дивизион 3 (1248 MMR)", "ГЧ1 (1537 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/SRG%20stormfv/overview"),
    (853216552, "Cylics", "fe5a998215454a77b493d074e2c5234a", "pupupu67", "Чемпион 2 / Дивизион 2 (1215 MMR)", "ГЧ1 (1435 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/%C6%A6%E2%84%A8%C4%AC/overview?utm_source=landing&utm_medium=profile-link&utm_campaign=landing-v2"),
    (892953049, "qwelyx", "Qwelyx.", "Walak.", "Чемпион 3 / Дивизион 1 (1315 MMR)", "ГЧ1 (1435 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/Qwelyx./overview"),
    (984566385, "zxdaqwd", "g0tthejuice", "1006872", "Чемпион 1 / Дивизион 4 (1162 MMR)", "Чемпион 2 / Дивизион 4 (1282 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/g0tthejuice/overview"),
    (1696948772, "furrynigger69", "Lev1k40", "levandosik_kakosik", "Чемпион 3 / Дивизион 1 (1315 MMR)", "Чемпион 3 / Дивизион 4 (1402 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/Lev1k40/overview"),
    (2097749803, "Korrya76", "KORRYA_mc", "Korrya76", "Даймонд 1 / Дивизион 3 (873 MMR)", "Чемпион 1 / Дивизион 2 (1095 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/Korrya_Mc/overview"),
    (6424764691, "Саня", "w1nbl", "w1nbl_", "Чемпион 2 / Дивизион 1 (1195 MMR)", "Чемпион 2 / Дивизион 1 (1195 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/w1nbl/overview"),
    (8420004944, "Popolovnik", "DSoymon4ik", "dsoymon4ik.", "Даймонд 3 / Дивизион 4 (1052 MMR)", "Чемпион 1 / Дивизион 1 (1075 MMR)", "https://rocketleague.tracker.network/rocket-league/profile/epic/DSoymon4ik/overview"),
]

def main():
    if not TURSO_URL or not TURSO_TOKEN:
        print("❌ TURSO_URL и TURSO_TOKEN не настроены!")
        sys.exit(1)

    print(f"🔗 Turso URL: {TURSO_URL[:50]}...")
    print(f"🔑 Token: {'✅' if TURSO_TOKEN else '❌'}")

    import libsql_experimental
    conn = libsql_experimental.connect(TURSO_URL, auth_token=TURSO_TOKEN)

    # Создаём таблицу если нет
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY, username TEXT, epic TEXT,
        discord TEXT, rank TEXT, peak_rank TEXT, tracker TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()

    # Считаем до
    cur = conn.execute("SELECT COUNT(*) FROM users")
    count_before = cur.fetchone()[0]
    print(f"\n📊 До импорта: {count_before} пользователей")

    added = 0
    skipped = 0
    errors = 0

    print(f"\n📋 Импорт {len(PLAYERS)} игроков...\n")

    for tg_id, username, epic, discord, rank, peak_rank, tracker in PLAYERS:
        try:
            # Проверяем есть ли уже
            cur = conn.execute("SELECT tg_id FROM users WHERE tg_id = ?", (tg_id,))
            if cur.fetchone():
                print(f"⏭️  @{username} — уже в БД")
                skipped += 1
                continue

            # Вставляем
            conn.execute(
                "INSERT INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tg_id, username, epic, discord, rank, peak_rank, tracker)
            )
            conn.commit()
            print(f"✅ @{username} ({tg_id}) — добавлен")
            added += 1
        except Exception as e:
            print(f"❌ @{username} ({tg_id}): {e}")
            errors += 1

    # Считаем после
    cur = conn.execute("SELECT COUNT(*) FROM users")
    count_after = cur.fetchone()[0]
    print(f"\n📊 После импорта: {count_after} пользователей")

    # Показываем всех
    print(f"\n📋 Все игроки в БД:")
    cur = conn.execute("SELECT tg_id, username, epic FROM users ORDER BY username")
    for row in cur.fetchall():
        print(f"   @{row[1]} | {row[0]} | Epic: {row[2]}")

    conn.close()

    print(f"\n{'─' * 50}")
    print(f"✅ Добавлено:  {added}")
    print(f"⏭️  Пропущено: {skipped}")
    if errors:
        print(f"❌ Ошибок:    {errors}")
    print(f"{'─' * 50}")
    print("Готово! Игроки теперь видны в админ-панели бота.")

if __name__ == "__main__":
    main()