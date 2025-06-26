import asyncio
import functools
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from typing import Optional

from src import config
from src.context import database
from src.ingest.handler import handle_message
from src.bot import command_handler
from src.scheduler.jobs import run_scheduler

async def main():
    """Main entry point to run the user client and the bot client concurrently."""
    
    # 1. Initialize Database
    database.init_db()

    # 2. Initialize Telethon User Client
    user_session = StringSession(config.USER_SESSION_STRING) if config.USER_SESSION_STRING else 'user_session'
    user_client = TelegramClient(
        user_session,
        config.APP_ID,
        config.APP_HASH
    )
    
    # 3. Initialize PTB Bot Application
    bot_app: Optional[Application] = None
    if config.NOTIFIER_BOT_TOKEN:
        bot_app = Application.builder().token(config.NOTIFIER_BOT_TOKEN).build()
        # Register command handlers
        bot_app.add_handler(CommandHandler("done", command_handler.done_command))
        bot_app.add_handler(CommandHandler("tasks", command_handler.tasks_command))
        bot_app.add_handler(CommandHandler("completed", command_handler.completed_command))
        bot_app.add_handler(CommandHandler("help", command_handler.help_command))
        # Add a handler for unknown commands
        bot_app.add_handler(MessageHandler(filters.COMMAND, command_handler.unknown_command))
    else:
        print("⚠️ Notifier bot token not set, command handling will be disabled.")


    # 4. Register Event Handlers for User Client
    user_handler = functools.partial(handle_message, client=user_client)
    user_client.on(events.NewMessage())(user_handler)

    # 5. Start clients and run concurrently
    try:
        await user_client.start() # type: ignore
        print(f"🚀 Copilot User is running...")

        # Create a list of tasks to run concurrently
        tasks = [asyncio.create_task(user_client.run_until_disconnected())] # type: ignore

        if bot_app and bot_app.updater:
            print(f"🚀 Notifier Bot is running...")
            # Initialize and start the bot application
            await bot_app.initialize()
            await bot_app.start()
            await bot_app.updater.start_polling()
            
            # Start scheduler with both clients
            asyncio.create_task(run_scheduler(user_client, bot_app.bot))
        else:
            print("⚠️ Notifier bot token not set, scheduler will not send notifications via bot.")
            # Start scheduler with only user client
            asyncio.create_task(run_scheduler(user_client, None))
            
        # Wait for all running clients to disconnect
        # The bot is handled by its own tasks, just need to await the user client here
        # and the graceful shutdown in the finally block will handle the bot.
        await asyncio.gather(*tasks)

    except Exception as e:
        print(f"🚨 An error occurred: {e}")
    finally:
        # Ensure clients are disconnected on exit
        if bot_app and bot_app.updater:
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        if user_client.is_connected():
            await user_client.disconnect() # type: ignore


if __name__ == "__main__":
    asyncio.run(main()) 