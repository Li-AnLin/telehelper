import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
import datetime

# Load environment variables from .env file
load_dotenv()

app_id = int(os.getenv("APP_ID"))
app_hash = os.getenv("APP_HASH")
app_title = "TeleHelper"

# 初始化 Telegram 用戶端
client = TelegramClient(app_title, app_id, app_hash)

@client.on(events.NewMessage)
async def handle_message(event):
    sender = await event.get_sender()
    sender_name = sender.username or sender.first_name or "未知"
    text = event.message.message

    # 可加入關鍵字篩選
    keywords = ['幫我', '請你', '麻煩', '記得']
    if any(kw in text.lower() for kw in keywords):
        print("=" * 40)
        print(f"🕐 {datetime.datetime.now()}")
        print(f"👤 來自：{sender_name}")
        print(f"💬 訊息：{text}")
        print("=" * 40)

client.start()
print("🚀 Telegram 監聽中... 按 Ctrl+C 停止")
client.run_until_disconnected()