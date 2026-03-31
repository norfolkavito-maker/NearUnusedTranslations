import asyncio
from datetime import datetime
from aiogram import Bot
from db import get_all_users, get_pending_notifications, mark_notification_sent


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


async def scheduler_task(bot: Bot):
    """Background task for checking notifications"""
    while True:
        try:
            await check_notifications(bot)
        except Exception as e:
            print(f"Scheduler error: {e}")
        
        # Check every minute
        await asyncio.sleep(60)
