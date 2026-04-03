import asyncio
from datetime import datetime
from aiogram import Bot
from db import get_all_users, get_pending_notifications, mark_notification_sent, create_backup, log_bot

# Событие для остановки планировщика
_stop_event = asyncio.Event()

# Счётчик для автоматического бэкапа (каждые 6 часов = 360 проверок)
_AUTO_BACKUP_INTERVAL = 360
_backup_counter = 0


def stop_scheduler():
    """Остановить планировщик"""
    _stop_event.set()


async def check_notifications(bot: Bot):
    """Check and send pending notifications"""
    try:
        notifications = await get_pending_notifications()
        users = await get_all_users()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for notification in notifications:
            if notification["send_time"] <= current_time:
                # Send notification to all users
                for user in users:
                    try:
                        await bot.send_message(
                            chat_id=user["tg_id"],
                            text=notification["message"],
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"Failed to send notification to {user['tg_id']}: {e}")
                
                # Mark as sent
                await mark_notification_sent(notification["id"])
                print(f"Notification {notification['id']} sent to {len(users)} users")
    except Exception as e:
        print(f"Error in check_notifications: {e}")


async def auto_backup():
    """Автоматический бэкап каждые 6 часов"""
    global _backup_counter
    _backup_counter += 1
    
    if _backup_counter >= _AUTO_BACKUP_INTERVAL:
        _backup_counter = 0
        try:
            backup_json = await create_backup()
            if backup_json:
                await log_bot("AUTO_BACKUP", "Автоматический бэкап создан успешно")
                print("💾 Автоматический бэкап создан")
        except Exception as e:
            await log_bot("AUTO_BACKUP_ERROR", f"Ошибка: {e}")
            print(f"❌ Ошибка автоматического бэкапа: {e}")


async def scheduler_task(bot: Bot):
    """Background task for checking notifications and auto backup"""
    print("✅ Планировщик уведомлений и бэкапов запущен")
    while not _stop_event.is_set():
        try:
            await check_notifications(bot)
            await auto_backup()
        except Exception as e:
            print(f"Scheduler error: {e}")
        
        # Check every minute, but can be stopped
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=60)
            break  # Если событие установлено - выходим
        except asyncio.TimeoutError:
            pass  # Таймаут истёк, продолжаем работу
    
    print("🛑 Планировщик уведомлений и бэкапов остановлен")
