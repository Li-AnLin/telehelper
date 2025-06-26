import asyncio
import functools
from telethon import TelegramClient, events

from src import config
from src.context import database
from src.ingest.handler import handle_message
from src.bot.command_handler import handle_bot_command
from src.scheduler.jobs import run_scheduler
from typing import Optional

async def main():
    """Main entry point to run the user client and the bot client concurrently."""
    
    # 1. Initialize Database
    database.init_db()

    # 2. Initialize Clients
    user_client = TelegramClient(
        'user_session',
        config.APP_ID,
        config.APP_HASH
    )
    
    bot_client: Optional[TelegramClient] = None
    if config.NOTIFIER_BOT_TOKEN:
        bot_client = TelegramClient(
            'notifier_bot_session',
            config.APP_ID,
            config.APP_HASH
        )

    # 3. Register Event Handlers
    # User client handles message ingestion
    user_handler = functools.partial(handle_message, client=user_client)
    user_client.on(events.NewMessage())(user_handler)
    
    # Bot client handles commands (if enabled)
    if bot_client:
        bot_client.on(events.NewMessage(incoming=True))(handle_bot_command)
    else:
        print("⚠️ Notifier bot token not set, command handling will be disabled.")

    # 4. Start clients and run concurrently
    try:
        await user_client.start() # type: ignore
        print(f"🚀 Copilot User is running...")

        # Create a list of tasks to run concurrently
        tasks = [asyncio.create_task(user_client.run_until_disconnected())] # type: ignore

        if bot_client:
            await bot_client.start(bot_token=config.NOTIFIER_BOT_TOKEN) # type: ignore
            print(f"🚀 Notifier Bot is running...")
            tasks.append(asyncio.create_task(bot_client.run_until_disconnected())) # type: ignore
            
            # Start scheduler with both clients
            asyncio.create_task(run_scheduler(user_client, bot_client))
        else:
            print("⚠️ Notifier bot token not set, scheduler will not send notifications via bot.")
            # Start scheduler with only user client (bot_client will be None)
            asyncio.create_task(run_scheduler(user_client, None))
            
        # Wait for all running clients to disconnect
        await asyncio.gather(*tasks) # type: ignore

    except Exception as e:
        print(f"🚨 An error occurred: {e}")
    finally:
        # Ensure clients are disconnected on exit
        if user_client.is_connected():
            await user_client.disconnect() # type: ignore
        if bot_client and bot_client.is_connected():
            await bot_client.disconnect() # type: ignore

if __name__ == "__main__":
    asyncio.run(main()) 