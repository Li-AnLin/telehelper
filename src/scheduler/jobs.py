import asyncio
import datetime
from telethon import TelegramClient
from src.context import database
from src.bot import notifier
from typing import Optional
import aiocron
from src import config

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
    """Runs the daily summary job at a fixed time every day using cron format."""
    print(f"Scheduling daily summary with cron: {config.DAILY_SUMMARY_CRON}")
    
    # Schedule the daily summary task using aiocron
    # The function needs to be a partial to pass arguments to it
    daily_summary_task = aiocron.crontab(
        config.DAILY_SUMMARY_CRON,
        func=send_daily_summary,
        args=(user_client, bot_client),
        start=True, # Start the cron job immediately
        loop=asyncio.get_running_loop() # Ensure it runs on the current loop
    )
    print("Scheduler started. Waiting for cron job to trigger...")
    # The scheduler runs indefinitely in the background, so no need for a while True loop here 