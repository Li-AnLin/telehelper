import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession

# It's better to ask user directly than reading config file
# to make this script more standalone.

async def main():
    print("This script will help you generate a Telethon session string.")
    print("You will need your Telegram API ID and API Hash.")
    print("You can get them from my.telegram.org.")
    
    try:
        app_id = int(input("Please enter your App ID: "))
        app_hash = input("Please enter your App Hash: ")
    except ValueError:
        print("Invalid App ID. It should be a number.")
        return

    print("\\nStarting session string generator...")
    print("You will be prompted for your phone number, password (if any), and login code.")

    # Using StringSession() will store the session in memory, not in a file
    async with TelegramClient(StringSession(), app_id, app_hash) as client:
        # The client will connect and prompt for login details automatically.
        # Calling a method like get_me() ensures we are logged in.
        await client.get_me()
        
        session_string = client.session.save()
        print("\\n✅ Your session string is ready!\\n")
        print(session_string)
        print("\\nNOTE: This string gives full access to your account. Treat it like a password!")
        print("You can now set this string as the USER_SESSION_STRING environment variable for the main application.")
        

if __name__ == "__main__":
    # On Windows, the default asyncio event loop policy can cause issues with Telethon.
    # We set it to a compatible one if we detect we are on Windows.
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 