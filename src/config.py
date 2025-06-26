import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Telegram API ---
APP_ID = int(os.getenv("APP_ID", 0))
APP_HASH = os.getenv("APP_HASH", "")

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Bot Settings ---
# List of group IDs, titles, or usernames to ignore
IGNORE_GROUPS_STR = os.getenv("IGNORE_GROUPS", "")
IGNORE_GROUPS = []
if IGNORE_GROUPS_STR:
    # Split by comma and strip whitespace
    temp_groups = [item.strip() for item in IGNORE_GROUPS_STR.split(",") if item.strip()]
    # Convert numeric strings to integers for group IDs
    for item in temp_groups:
        try:
            IGNORE_GROUPS.append(int(item))
        except ValueError:
            # Keep as string if it's not a number (username or title)
            IGNORE_GROUPS.append(item)

# --- Scheduler Settings ---
# Time to send daily summary (HH:MM) - DEPRECATED, use DAILY_SUMMARY_CRON
# SUMMARY_TIME = "09:00"
DAILY_SUMMARY_CRON = os.getenv("DAILY_SUMMARY_CRON", "0 9 * * *") # default to 09:00 daily

# --- Notifier Bot Settings ---
# Bot token for sending notifications from @BotFather
NOTIFIER_BOT_TOKEN = os.getenv("NOTIFIER_BOT_TOKEN", "")
# Your personal chat ID to receive notifications
# You can get this from a bot like @userinfobot
NOTIFIER_TARGET_CHAT_ID = int(os.getenv("NOTIFIER_TARGET_CHAT_ID", 0))

# --- User Settings ---
TELEGRAM_USER_NAME = os.getenv("TELEGRAM_USER_NAME", "主人")

# --- Database ---
DB_NAME = "tasks.db" 