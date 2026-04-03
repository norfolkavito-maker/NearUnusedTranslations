#!/usr/bin/env python3
"""
Скрипт импорта 8 существующих игроков в базу данных Turso.

Запуск через Railway CLI:
    railway shell
    python import_players.py

Скрипт проверяет наличие каждого игрока перед добавлением — дубликаты не создаются.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, _safe_query, _fetchone
from config import TURSO_URL, TURSO_TOKEN

PLAYERS = [
    {
        "tg_id": 820870350,
        "username": "valiauh",
        "epic": "de7cce031eb04b0db7d2c8922738bbc7",
        "discord": "valiauh",
        "rank": "Чемпион 2 / Дивизион 3 (1248 MMR)",
        "peak_rank": "ГЧ1 (1537 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/SRG%20stormfv/overview",
    },
    {
        "tg_id": 853216552,
        "username": "Cylics",
        "epic": "fe5a998215454a77b493d074e2c5234a",
        "discord": "pupupu67",
        "rank": "Чемпион 2 / Дивизион 2 (1215 MMR)",
        "peak_rank": "ГЧ1 (1435 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/%C6%A6%E2%84%A8%C4%AC/overview?utm_source=landing&utm_medium=profile-link&utm_campaign=landing-v2",
    },
    {
        "tg_id": 892953049,
        "username": "qwelyx",
        "epic": "Qwelyx.",
        "discord": "Walak.",
        "rank": "Чемпион 3 / Дивизион 1 (1315 MMR)",
        "peak_rank": "ГЧ1 (1435 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/Qwelyx./overview",
    },
    {
        "tg_id": 984566385,
        "username": "zxdaqwd",
        "epic": "g0tthejuice",
        "discord": "1006872",
        "rank": "Чемпион 1 / Дивизион 4 (1162 MMR)",
        "peak_rank": "Чемпион 2 / Дивизион 4 (1282 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/g0tthejuice/overview",
    },
    {
        "tg_id": 1696948772,
        "username": "furrynigger69",
        "epic": "Lev1k40",
        "discord": "levandosik_kakosik",
        "rank": "Чемпион 3 / Дивизион 1 (1315 MMR)",
        "peak_rank": "Чемпион 3 / Дивизион 4 (1402 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/Lev1k40/overview",
    },
    {
        "tg_id": 2097749803,
        "username": "Korrya76",
        "epic": "KORRYA_mc",
        "discord": "Korrya76",
        "rank": "Даймонд 1 / Дивизион 3 (873 MMR)",
        "peak_rank": "Чемпион 1 / Дивизион 2 (1095 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/Korrya_Mc/overview",
    },
    {
        "tg_id": 6424764691,
        "username": "Саня",
        "epic": "w1nbl",
        "discord": "w1nbl_",
        "rank": "Чемпион 2 / Дивизион 1 (1195 MMR)",
        "peak_rank": "Чемпион 2 / Дивизион 1 (1195 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/w1nbl/overview",
    },
    {
        "tg_id": 8420004944,
        "username": "Popolovnik",
        "epic": "DSoymon4ik",
        "discord": "dsoymon4ik.",
        "rank": "Даймонд 3 / Дивизион 4 (1052 MMR)",
        "peak_rank": "Чемпион 1 / Дивизион 1 (1075 MMR)",
        "tracker": "https://rocketleague.tracker.network/rocket-league/profile/epic/DSoymon4ik/overview",
    },
]


async def main():
    if not TURSO_URL or not TURSO_TOKEN:
        print("❌ TURSO_URL и TURSO_TOKEN не настроены!")
        print(f"   TURSO_URL: {'✅' if TURSO_URL else '❌'}")
        print(f"   TURSO_TOKEN: {'✅' if TURSO_TOKEN else '❌'}")
        sys.exit(1)

    print(f"🔗 Подключение к Turso: {TURSO_URL[:60]}...")
    print("🗄️  Инициализация таблиц БД...")
    await init_db()

    # Проверим сколько сейчас пользователей
    cur = await _safe_query("SELECT COUNT(*) FROM users")
    if cur:
        row = _fetchone(cur)
        print(f"📊 Сейчас в БД: {row[0] if row else 0} пользователей")

    added = 0
    skipped = 0
    errors = 0

    print(f"\n📋 Импорт {len(PLAYERS)} игроков...\n")

    for player in PLAYERS:
        try:
            # Прямая проверка существования
            cur = await _safe_query("SELECT tg_id FROM users WHERE tg_id = ?", (player["tg_id"],))
            exists = False
            if cur:
                row = _fetchone(cur)
                exists = row is not None

            if exists:
                print(f"⏭️  Пропущен  @{player['username']} ({player['tg_id']}) — уже в БД")
                skipped += 1
                continue

            # Прямой INSERT
            await _safe_query(
                "INSERT OR REPLACE INTO users (tg_id, username, epic, discord, rank, peak_rank, tracker) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (player["tg_id"], player["username"], player["epic"], player["discord"],
                 player["rank"], player["peak_rank"], player["tracker"])
            )
            print(f"✅ Добавлен   @{player['username']} ({player['tg_id']}) | Epic: {player['epic']}")
            added += 1
        except Exception as e:
            print(f"❌ Ошибка    @{player['username']} ({player['tg_id']}): {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    # Финальная проверка
    cur = await _safe_query("SELECT COUNT(*) FROM users")
    if cur:
        row = _fetchone(cur)
        print(f"\n📊 Теперь в БД: {row[0] if row else 0} пользователей")

    print(f"\n{'─' * 50}")
    print(f"✅ Добавлено:  {added}")
    print(f"⏭️  Пропущено: {skipped}")
    if errors:
        print(f"❌ Ошибок:    {errors}")
    print(f"{'─' * 50}")
    print("Импорт завершён.")


if __name__ == "__main__":
    asyncio.run(main())