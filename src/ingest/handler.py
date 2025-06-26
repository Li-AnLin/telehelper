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
    if event.is_reply:
        # In topics, a message can be a reply to the topic starter (which we ignore) 
        # or a direct reply to a specific message.
        # A direct reply in a topic has reply_to_msg_id != reply_to_top_id.
        # A normal chat reply has reply_to_top_id = None.
        is_topic_direct_reply = (
            event.message.reply_to and
            event.message.reply_to.reply_to_top_id and
            event.message.reply_to.reply_to_msg_id != event.message.reply_to.reply_to_top_id
        )
        is_normal_chat_reply = event.message.reply_to and not event.message.reply_to.reply_to_top_id

        if is_topic_direct_reply or is_normal_chat_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg and getattr(reply_msg.from_id, 'user_id', None) == me.id:
                return True

    return False

def get_sender_name(sender):
    """Extracts a display name from the sender object."""
    if not sender:
        return "Unknown"
    if isinstance(sender, User):
        return sender.first_name or sender.last_name or sender.username or "Unknown"
    return "Unknown"

async def create_task_from_event(event, sender_name: str):
    """Creates a task dictionary from a message event."""
    task_data = {
        'source': 'telegram',
        'chat_id': event.chat_id,
        'message_id': event.message.id,
        'sender': sender_name,
        'content': event.message.message,
        'detected_at': datetime.datetime.now().isoformat(),
        'completed_at': None,
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
    # Filter my message being forwarded
    # 1. if the message content is the canned reply, ignore it
    if text.strip() == config.TASK_ADDED_REPLY:
        print("Ignoring canned reply message.")
        return
    # 2. if the message is forwarded and the original sender_id is myself
    if getattr(event.message, 'forward', None):
        forward_sender_id = getattr(getattr(event.message.forward, 'sender', None), 'id', None) or \
                            getattr(event.message.forward, 'sender_id', None)
        if forward_sender_id == getattr(me, 'id', None):
            print("Ignoring forwarded canned reply from myself.")
            return

    sender = await event.get_sender()
    # Ignore messages from bots
    if getattr(sender, 'bot', False):
        print(f"Ignoring message from bot: {getattr(sender, 'username', 'Unknown')}")
        return
    # Ignore messages sent by myself
    if getattr(sender, 'id', None) == getattr(me, 'id', None):
        print("Ignoring message sent by myself.")
        return

    sender_name = get_sender_name(sender)
    
    should_process = False
    if event.is_private:
        # For private chats, check with LLM
        if await llm_client.is_task(text):
            should_process = True
    elif await is_tagged(event, me):
        # For groups, only process if mentioned
        if await llm_client.is_task(text):
            should_process = True

    if should_process:
        print(f"Detected potential task from {sender_name} in chat {event.chat_id}.")
        await create_task_from_event(event, sender_name)
        # Optionally, send a confirmation reply
        await event.reply(config.TASK_ADDED_REPLY) 