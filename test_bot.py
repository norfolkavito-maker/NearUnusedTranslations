import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = os.getenv("TOKEN", "")

async def main():
    if not TOKEN:
        print("❌ TOKEN не установлен!")
        return
    
    print("🚀 Запуск тестового бота...")
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    @dp.message(Command("start"))
    async def cmd_start(msg: Message):
        await msg.answer("✅ Бот работает!")
        print(f"✅ Получено сообщение от {msg.from_user.id}")
    
    try:
        print(f"✅ Bot создан: @{(await bot.get_me()).username}")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
