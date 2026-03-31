import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

# Импорты для теста
try:
    from db import init_db, add_admin, get_all_admins, count_users
    print("✅ Импорт БД успешен")
except Exception as e:
    print(f"❌ Ошибка импорта БД: {e}")

TOKEN = os.getenv("TOKEN", "")

async def test_db():
    print("\n🗄️ Тестирование БД...")
    try:
        await init_db()
        print("✅ БД инициализирована")
        
        # Тест добавления админа
        await add_admin(123456789, "test_user", 111111111)
        print("✅ Админ добавлен")
        
        # Тест получения админов
        admins = await get_all_admins()
        print(f"✅ Получено админов: {len(admins)}")
        
        # Тест подсчета пользователей
        count = await count_users()
        print(f"✅ Пользователей в БД: {count}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot():
    print("\n🤖 Тестирование бота...")
    if not TOKEN:
        print("❌ TOKEN не установлен")
        return False
    
    try:
        bot = Bot(token=TOKEN)
        me = await bot.get_me()
        print(f"✅ Бот создан: @{me.username}")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")
        return False

async def test_handlers():
    print("\n🎮 Тестирование обработчиков...")
    try:
        from handlers import admin_manage_id, admin_list
        print("✅ Обработчики импортированы")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта обработчиков: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔍 ПОЛНАЯ ДИАГНОСТИКА БОТА")
    print("=" * 50)
    
    # Тест БД
    db_ok = await test_db()
    
    # Тест бота
    bot_ok = await test_bot()
    
    # Тест обработчиков
    handlers_ok = await test_handlers()
    
    print("\n📊 ИТОГИ:")
    print(f"БД: {'✅' if db_ok else '❌'}")
    print(f"Бот: {'✅' if bot_ok else '❌'}")
    print(f"Обработчики: {'✅' if handlers_ok else '❌'}")
    
    if all([db_ok, bot_ok, handlers_ok]):
        print("\n🎉 Все компоненты работают!")
    else:
        print("\n⚠️ Есть проблемы - см. ошибки выше")
    
    # Простой бот для теста кнопок
    if bot_ok:
        await test_simple_bot()

async def test_simple_bot():
    print("\n🎯 Запуск тестового бота для кнопок...")
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    @dp.message(Command("start"))
    async def cmd_start(msg: Message):
        await msg.answer("✅ Тестовый бот работает!")
        print(f"✅ Получено /start от {msg.from_user.id}")
    
    @dp.message(Command("test_db"))
    async def cmd_test_db(msg: Message):
        try:
            admins = await get_all_admins()
            await msg.answer(f"📊 Админов в БД: {len(admins)}")
            print(f"✅ Проверка БД от {msg.from_user.id}")
        except Exception as e:
            await msg.answer(f"❌ Ошибка БД: {e}")
    
    print("🚀 Тестовый бот запущен...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка тестового бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
