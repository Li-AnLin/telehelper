from telethon import TelegramClient
from src import config
from typing import Optional

async def send_notification(client: TelegramClient, message: str):
    """
    Sends a message using the dedicated notifier bot client.
    """
    if not config.NOTIFIER_TARGET_CHAT_ID:
        print("⚠️ WARNING: Notifier target chat ID is not set. Cannot send notification.")
        return

    try:
        await client.send_message(
            config.NOTIFIER_TARGET_CHAT_ID,
            message,
            parse_mode='md'
        )
        print("Notification sent successfully via bot.")
    except Exception as e:
        print(f"🚨 ERROR sending notification via bot: {e}") 