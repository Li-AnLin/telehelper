import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

from src import config
from src.context import database
from src.bot.bot_wrapper import TelegramBotWrapper


def create_user_client() -> TelegramClient:
    """創建並配置 Telethon User Client"""
    user_session = StringSession(config.USER_SESSION_STRING) if config.USER_SESSION_STRING else 'user_session'
    return TelegramClient(
        user_session,
        config.APP_ID,
        config.APP_HASH
    )


async def main():
    """Main entry point to run the user client and the bot client concurrently."""
    
    # 1. Initialize Database
    database.init_db()

    # 2. Create User Client
    user_client = create_user_client()
    
    # 3. Create bot wrapper with injected user_client
    bot_wrapper = TelegramBotWrapper(user_client)
    
    if not await bot_wrapper.initialize():
        print("❌ Bot initialization failed")
        return
    
    # 4. Start user client first
    try:
        await user_client.start()  # type: ignore
        print("🚀 Copilot User is running...")
        
        # 5. Start the bot wrapper
        await bot_wrapper.start()
        
        # 6. Run user client until disconnected
        await user_client.run_until_disconnected()  # type: ignore
        
    except Exception as e:
        print(f"🚨 An error occurred: {e}")
    finally:
        # Ensure clients are disconnected on exit
        await bot_wrapper.stop()
        if user_client.is_connected():
            await user_client.disconnect()  # type: ignore


if __name__ == "__main__":
    asyncio.run(main()) 