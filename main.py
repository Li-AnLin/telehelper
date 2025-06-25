import asyncio
from src.bot.main import main

if __name__ == "__main__":
    # To avoid potential issues with asyncio loops on Windows,
    # it's good practice to set the event loop policy.
    # However, for simplicity, we'll rely on asyncio.run's default behavior.
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.") 