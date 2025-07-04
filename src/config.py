import yaml
import os
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Load config from YAML file
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config is None:
            config = {}
except FileNotFoundError:
    print("❌ config.yaml not found. Please copy config.yaml.example to config.yaml and fill in your details.")
    config = {} # Create an empty config dict to avoid crashes below
except yaml.YAMLError as e:
    print(f"❌ Error parsing config.yaml: {e}")
    config = {}

# --- Telegram API ---
telegram_config = config.get("telegram_api", {})
APP_ID = telegram_config.get("app_id", 0)
APP_HASH = telegram_config.get("app_hash", "")

# --- Gemini API ---
gemini_config = config.get("gemini_api", {})
GEMINI_API_KEY = gemini_config.get("api_key", "")

# --- Bot Settings ---
bot_settings_config = config.get("bot_settings", {})
IGNORE_GROUPS = bot_settings_config.get("ignore_groups", [])
TELEGRAM_USER_NAME = bot_settings_config.get("telegram_user_name", "Boss")
ENABLE_REPLY = bot_settings_config.get("enable_reply", True)
ENABLE_REPLY_IN_PRIVATE = bot_settings_config.get("enable_reply_in_private", True)
TASK_ADDED_REPLY = bot_settings_config.get("task_added_reply", "Note it.")

# --- Scheduler Settings ---
scheduler_config = config.get("scheduler", {})
DAILY_SUMMARY_CRON = scheduler_config.get("daily_summary_cron", "0 9 * * *")

# --- Notifier Bot Settings ---
notifier_config = config.get("notifier", {})
NOTIFIER_BOT_TOKEN = notifier_config.get("bot_token", "")
NOTIFIER_TARGET_CHAT_ID = notifier_config.get("target_chat_id", 0)

# --- Database ---
database_config = config.get("database", {})
DB_NAME = database_config.get("name", "tasks.db")

# --- Perform some checks for critical settings ---
if not APP_ID or not APP_HASH or APP_HASH == "your_app_hash":
    print("⚠️ Telegram App ID/Hash is not configured correctly in config.yaml.")

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key":
    print("⚠️ Gemini API Key is not configured in config.yaml.")

if not NOTIFIER_BOT_TOKEN or not NOTIFIER_TARGET_CHAT_ID or NOTIFIER_BOT_TOKEN == "your_notifier_bot_token":
    print("⚠️ Notifier Bot Token/Target Chat ID is not configured correctly in config.yaml.")

# --- Session Strings (for Docker/non-interactive environments) ---
# Read from environment variables. If not set, they will be None.
USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING")

if USER_SESSION_STRING:
    print("✅ User session string found in environment variables.")
else:
    print("ℹ️ User session string not found in environment variables. Will use 'user_session.session' file.") 