#!/usr/bin/env python3
"""
Скрипт проверки подключения к Turso.
Запускать на Railway Shell или локально:
  python check_turso.py

Использует переменные TURSA_URL и TURSA_TOKEN из config.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_connection():
    os.environ["TURSO_URL"] = os.getenv("TURSA_URL", "")
    os.environ["TURSO_TOKEN"] = os.getenv("TURSA_TOKEN", "")
    
    from config import TURSO_URL, TURSO_TOKEN
    
    print(f"🔗 TURSA_URL: {TURSO_URL[:50]}..." if TURSO_URL else "❌ TURSA_URL не настроен!")
    print(f"🔑 TURSA_TOKEN: {TURSO_TOKEN[:20]}..." if TURSO_TOKEN else "❌ TURSA_TOKEN не настроен!")
    
    if not TURSO_URL or not TURSO_TOKEN:
        print("\n❌ Проверьте переменные TURSA_URL и TURSA_TOKEN в Railway!")
        return
    
    try:
        import libsql_experimental
        conn = libsql_experimental.connect(TURSO_URL, auth_token=TURSO_TOKEN)
        
        # Получить все таблицы
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n✅ Подключение к Turso успешно!")
        print(f"\n📋 Таблицы в базе ({len(tables)}):")
        for (name,) in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
            print(f"   📄 {name} — {count} записей")
        
        # Показать данные пользователей
        cursor = conn.execute("SELECT tg_id, username, epic FROM users ORDER BY username LIMIT 20")
        rows = cursor.fetchall()
        if rows:
            print(f"\n👥 Пользователи ({len(rows)}):")
            for tg_id, username, epic in rows:
                print(f"   @{username} | ID: {tg_id} | Epic: {epic}")
        else:
            print("\n⚠️ Таблица users пуста!")
        
    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_connection()