#!/usr/bin/env python3
"""
Скрипт импорта 13 существующих игроков в базу данных Turso.

Запуск через Railway CLI:
    railway shell
    python import_players.py

Скрипт проверяет наличие каждого игрока перед добавлением — дубликаты не создаются.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, add_user, check_user
from config import TURSO_URL, TURSO_TOKEN

PLAYERS = [
    {
        "tg_id": 820870350,
        "username": "valiauh",
        "epic": "de7cce031eb04b0db7d2c8922738bbc7",
        "discord": "valiauh",
        "rank": "Чемпион 2 / Дивизион 3 (1248 MMR)",
        "peak_rank": "ГЧ1 (1537 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 853216552,
        "username": "Cylics",
        "epic": "fe5a998215454a77b493d074e2c5234a",
        "discord": "pupupu67",
        "rank": "Чемпион 2 / Дивизион 2 (1215 MMR)",
        "peak_rank": "ГЧ1 (1435 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 892953049,
        "username": "qwelyx",
        "epic": "Qwelyx.",
        "discord": "Walak.",
        "rank": "Чемпион 3 / Дивизион 1 (1315 MMR)",
        "peak_rank": "ГЧ1 (1435 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 984566385,
        "username": "zxdaqwd",
        "epic": "g0tthejuice",
        "discord": "1006872",
        "rank": "Чемпион 1 / Дивизион 4 (1162 MMR)",
        "peak_rank": "Чемпион 2 / Дивизион 4 (1282 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 1027866429,
        "username": "almuted",
        "epic": "Schmurdya",
        "discord": "schmurdya",
        "rank": "MMR: 1070",
        "peak_rank": "Чемпион 3 / Дивизион 2 (1335 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 1455661269,
        "username": "CheSlychilos",
        "epic": "ForgetMyName_",
        "discord": "piredozzza",
        "rank": "Чемпион 1 / Дивизион 4 (1162 MMR)",
        "peak_rank": "Чемпион 3 / Дивизион 3 (1372 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 1696948772,
        "username": "furrynigger69",
        "epic": "Lev1k40",
        "discord": "levandosik_kakosik",
        "rank": "Чемпион 3 / Дивизион 1 (1315 MMR)",
        "peak_rank": "Чемпион 3 / Дивизион 4 (1402 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 2097749803,
        "username": "Korrya76",
        "epic": "KORRYA_mc",
        "discord": "Korrya76",
        "rank": "Даймонд 1 / Дивизион 3 (873 MMR)",
        "peak_rank": "Чемпион 1 / Дивизион 2 (1095 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 5208295687,
        "username": "M1rpe",
        "epic": "4f78a67a7f444bf19f82f7acc309c093",
        "discord": "okeokeoka",
        "rank": "Чемпион 2 / Дивизион 3 (1248 MMR)",
        "peak_rank": "Чемпион 3 / Дивизион 1 (1315 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 5315781827,
        "username": "dinilama",
        "epic": "Бля(",
        "discord": "mvnicx",
        "rank": "Чемпион 1 / Дивизион 1 (1075 MMR)",
        "peak_rank": "Чемпион 1 / Дивизион 3 (1128 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 5975741277,
        "username": "ribmus",
        "epic": "Buchptz",
        "discord": "ribmus",
        "rank": "Даймонд 3 / Дивизион 1 (995 MMR)",
        "peak_rank": "Чемпион 1 / Дивизион 1 (1075 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 6424764691,
        "username": "Саня",
        "epic": "w1nbl",
        "discord": "w1nbl_",
        "rank": "Чемпион 2 / Дивизион 1 (1195 MMR)",
        "peak_rank": "Чемпион 2 / Дивизион 1 (1195 MMR)",
        "tracker": "",
    },
    {
        "tg_id": 8420004944,
        "username": "Popolovnik",
        "epic": "DSoymon4ik",
        "discord": "dsoymon4ik.",
        "rank": "Даймонд 3 / Дивизион 4 (1052 MMR)",
        "peak_rank": "Чемпион 1 / Дивизион 1 (1075 MMR)",
        "tracker": "",
    },
]


async def main():
    # Validate environment before doing anything
    if not TURSO_URL or not TURSO_TOKEN:
        print("❌ TURSO_URL и TURSO_TOKEN не настроены!")
        print("   Убедитесь, что переменные окружения заданы в Railway.")
        sys.exit(1)

    print(f"🔗 Подключение к Turso: {TURSO_URL[:60]}...")
    print("🗄️  Инициализация таблиц БД...")
    await init_db()

    added = 0
    skipped = 0
    errors = 0

    print(f"\n📋 Импорт {len(PLAYERS)} игроков...\n")

    for player in PLAYERS:
        try:
            exists = await check_user(player["tg_id"])
            if exists:
                print(f"⏭️  Пропущен  @{player['username']} ({player['tg_id']}) — уже в БД")
                skipped += 1
                continue

            await add_user(
                tg_id=player["tg_id"],
                username=player["username"],
                epic=player["epic"],
                discord=player["discord"],
                rank=player["rank"],
                peak_rank=player["peak_rank"],
                tracker=player["tracker"],
            )
            print(
                f"✅ Добавлен   @{player['username']} ({player['tg_id']}) | "
                f"Epic: {player['epic']} | MMR: {player['rank']}"
            )
            added += 1
        except Exception as e:
            print(f"❌ Ошибка    @{player['username']} ({player['tg_id']}): {e}")
            errors += 1

    print(f"\n{'─' * 50}")
    print(f"✅ Добавлено:  {added}")
    print(f"⏭️  Пропущено: {skipped}")
    if errors:
        print(f"❌ Ошибок:    {errors}")
    print(f"{'─' * 50}")
    print("Импорт завершён.")


if __name__ == "__main__":
    asyncio.run(main())
