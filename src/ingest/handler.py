from telethon import events, TelegramClient
from telethon.tl.types import User
import datetime

from src import config
from src.llm import client as llm_client
from src.context import database

def is_ignored_group(event, chat):
    """Checks if the message is from an ignored group."""
    group_id = event.chat_id
    chat_title = getattr(chat, 'title', '')
    chat_username = getattr(chat, 'username', '')

    if event.is_group:
        if group_id in config.IGNORE_GROUPS or chat_title in config.IGNORE_GROUPS or chat_username in config.IGNORE_GROUPS:
            return True
    return False

async def is_tagged(event, me: User):
    """Checks if the user was mentioned in the message."""
    my_username = getattr(me, 'username', '').lower() if getattr(me, 'username', '') else ""
    text = event.message.message or ""
    if my_username and f"@{my_username}" in text.lower():
        return True
    
    # Check for replies to our messages
    if await event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg and getattr(reply_msg.from_id, 'user_id', None) == me.id:
            return True

    return False

def filter_keywords(text: str):
    """Checks for keywords in private messages to decide if it's worth checking with LLM."""
    return any(kw in text.lower() for kw in config.PRIVATE_MESSAGE_KEYWORDS)

def get_sender_name(sender):
    """Extracts a display name from the sender object."""
    if not sender:
        return "未知"
    if isinstance(sender, User):
        return sender.username or sender.first_name or "未知"
    return "未知"

async def create_task_from_event(event, sender_name: str):
    """Creates a task dictionary from a message event."""
    task_data = {
        'source': 'telegram',
        'chat_id': event.chat_id,
        'message_id': event.message.id,
        'sender': sender_name,
        'content': event.message.message,
        'detected_at': datetime.datetime.now().isoformat(),
        'status': 'new',
        'tags': []
    }
    await database.add_task(task_data)

# This function will be registered as the event handler
async def handle_message(event: events.NewMessage.Event, client: TelegramClient):
    """The main message handler."""
    chat = await event.get_chat()
    me = await client.get_me()

    # Ensure we have a valid user object for "me"
    if not isinstance(me, User):
        print("Could not retrieve valid 'me' user object. Aborting.")
        return

    if is_ignored_group(event, chat):
        return

    text = event.message.message or ""
    if not text:
        return

    sender = await event.get_sender()
    sender_name = get_sender_name(sender)
    
    should_process = False
    if event.is_private:
        # For private chats, check for keywords or let LLM decide
        if filter_keywords(text):
            if await llm_client.is_task(text):
                should_process = True
    elif await is_tagged(event, me):
        # For groups, only process if mentioned
        should_process = True

    if should_process:
        print(f"Detected potential task from {sender_name} in chat {event.chat_id}.")
        await create_task_from_event(event, sender_name)
        # Optionally, send a confirmation reply
        await event.reply("好的，我已經將這則訊息記錄到待辦事項中了。") 