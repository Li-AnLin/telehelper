import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
import datetime
import asyncio

# Load environment variables from .env file
load_dotenv()

app_id = int(os.getenv("APP_ID", ""))
app_hash = os.getenv("APP_HASH", "")
app_title = "TeleHelper"

IGNORE_GROUPS = []

# 初始化 Telegram 用戶端
client = TelegramClient(app_title, app_id, app_hash)

def is_ignored_group(event, chat):
    group_id = event.chat_id
    chat_title = getattr(chat, 'title', '')
    chat_username = getattr(chat, 'username', '')


    # 檢查訊息是否來自被忽略的群組
    if event.is_group:
        if group_id in IGNORE_GROUPS or chat_title in IGNORE_GROUPS or chat_username in IGNORE_GROUPS:
            return True
    
    return False

async def is_tagged(event):
    me = await client.get_me()
    my_username = getattr(me, 'username', '').lower() if getattr(me, 'username', '') else ""

    # 判斷是否有 @自己（透過文字比對）
    text = event.message.message or ""
    if f"@{my_username}" not in text.lower():
        return False # 沒有 @ 就略過
    
    return True # 有 @ 就返回 True

def filter_keywords(text):
    # 可加入關鍵字篩選
    keywords = ['幫我', '請你', '麻煩', '記得', '請問', '能不能', '可不可以', '有沒有', '有空', '有時間']
    return any(kw in text.lower() for kw in keywords)

def print_message_info(chat, event):
    try:
        # 獲取發送者的資訊
        chat_title = getattr(chat, 'title', '')
        chat_username = getattr(chat, 'username', '')
        text = event.message.message

        # 打印訊息資訊
        print("=" * 40)
        print(f"🕐 {datetime.datetime.now()}")
        if chat_title:
            # 詳細檢查 sender 資訊
            if event.sender is None:
                print(f"⚠️ WARNING: event.sender 為 None")
                print(f"📊 DEBUG INFO:")
                print(f"   - chat_id: {event.chat_id}")
                print(f"   - message_id: {event.message.id}")
                print(f"   - from_id: {getattr(event.message, 'from_id', 'None')}")
                print(f"   - peer_id: {getattr(event.message, 'peer_id', 'None')}")
                print(f"   - chat type: {type(chat).__name__}")
                print(f"   - event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
                sender_name = "發送者資訊無法取得"
            else:
                sender_username = getattr(event.sender, 'username', None) or ""
                sender_first_name = getattr(event.sender, 'first_name', None) or ""
                sender_name = sender_username or sender_first_name or "未知"
            
            print(f"👥 群組名稱：{chat_title}")
            print(f"👤 發言者：{sender_name}")
        else:
            print(f"👤 私訊：{chat_username}")
        print(f"💬 訊息：{text}")
        print("=" * 40)
    except Exception as e:
        print("🚨 ERROR in print_message_info:")
        print(f"Exception: {type(e).__name__}: {e}")
        print(f"📊 FULL DEBUG INFO:")
        print(f"   - chat: {chat}")
        print(f"   - chat type: {type(chat).__name__}")
        print(f"   - chat attributes: {[attr for attr in dir(chat) if not attr.startswith('_')]}")
        print(f"   - event: {event}")
        print(f"   - event type: {type(event).__name__}")
        print(f"   - event.sender: {getattr(event, 'sender', 'No sender attribute')}")
        print(f"   - event.message: {getattr(event, 'message', 'No message attribute')}")
        if hasattr(event, 'message') and event.message:
            print(f"   - message attributes: {[attr for attr in dir(event.message) if not attr.startswith('_')]}")
        print("=" * 50)

@client.on(events.NewMessage())
async def handle_message(event: events.NewMessage.Event):
    chat = await event.get_chat()
    # 忽略特定群組的訊息
    if is_ignored_group(event, chat):
        return

    text = event.message.message
    # 私訊的情況下，過濾關鍵字
    if event.is_private:
        if not filter_keywords(text):
            return
    elif not await is_tagged(event): # 如果不是私訊，則檢查是否有 @ 自己
        return

    # 通過過濾條件後，獲取發送者的資訊
    print_message_info(chat, event)

client.start()
print("🚀 Telegram 監聽中... 按 Ctrl+C 停止")
client.run_until_disconnected()