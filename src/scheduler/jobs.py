import asyncio
import datetime
from telethon import TelegramClient
from src.context import database
from src.bot import notifier
from typing import Optional

async def send_daily_summary(user_client: TelegramClient, bot_client: Optional[TelegramClient]):
    """Fetches pending tasks and sends a summary to the user via the notifier bot."""
    print("Running daily summary job...")
    try:
        pending_tasks = await database.get_pending_tasks()

        message_content = ""
        if not pending_tasks:
            message_content = "🎉 Power，你今天沒有未處理事項，做得很好！"
        else:
            message_content = f"👋 Power，你今天還有 {len(pending_tasks)} 件未處理事項：\n\n"
            for i, task in enumerate(pending_tasks, 1):
                # Try to get chat title for context using the main client
                try:
                    chat = await user_client.get_entity(task['chat_id'])
                    chat_title = getattr(chat, 'title', '私訊')
                except Exception:
                    chat_title = f"未知對話 ({task['chat_id']})"
                
                # Use status to assign an icon
                status_icon = "🔴" if task['status'] == 'new' else "🟡"
                message_content += f"{i}. {status_icon} **[{chat_title}]** {task['content'][:50]}...\n"
            
            message_content += "\n你可以直接回覆此訊息 `/done <任務編號>` 來標記完成。"
        
        if bot_client: # Only send via bot if bot_client is available
            await notifier.send_notification(bot_client, message_content)
            print(f"Sent daily summary with {len(pending_tasks)} tasks via bot.")
        else:
            print("Notifier bot not available. Printing summary to console:")
            print(message_content) # Fallback to console if bot is not active
            print(f"Printed daily summary with {len(pending_tasks)} tasks to console.")

    except Exception as e:
        print(f"🚨 ERROR in send_daily_summary: {e}")

async def run_scheduler(user_client: TelegramClient, bot_client: Optional[TelegramClient]):
    """Runs the daily summary job at a fixed time every day."""
    # This is a simple scheduler. For production, consider a more robust library.
    while True:
        # For demonstration, this runs every 2 minutes.
        # For daily, use: await asyncio.sleep(24 * 60 * 60)
        await asyncio.sleep(120) 
        await send_daily_summary(user_client, bot_client) 