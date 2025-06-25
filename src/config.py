import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Telegram API ---
APP_ID = int(os.getenv("APP_ID", 0))
APP_HASH = os.getenv("APP_HASH", "")
APP_TITLE = os.getenv("APP_TITLE", "TeleHelper")

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Bot Settings ---
# List of group IDs, titles, or usernames to ignore
IGNORE_GROUPS = [
    1903761391,
]

# Keywords to trigger task detection in private messages
PRIVATE_MESSAGE_KEYWORDS = ['幫我', '請你', '麻煩', '記得', '請問', '能不能', '可不可以', '有沒有', '有空', '有時間']

# --- Scheduler Settings ---
# Time to send daily summary (HH:MM)
SUMMARY_TIME = "09:00"

# --- Notifier Bot Settings ---
# Bot token for sending notifications from @BotFather
NOTIFIER_BOT_TOKEN = os.getenv("NOTIFIER_BOT_TOKEN", "")
# Your personal chat ID to receive notifications
# You can get this from a bot like @userinfobot
NOTIFIER_TARGET_CHAT_ID = int(os.getenv("NOTIFIER_TARGET_CHAT_ID", 0))

# --- Database ---
DB_NAME = "tasks.db" 