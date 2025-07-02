import asyncio
import functools
from typing import Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src import config
from src.ingest.handler import handle_message
from src.bot import command_handler
from src.scheduler.jobs import run_scheduler


class TelegramBotWrapper:
    """包裝 Telegram 機器人的類別，整合 user_client 和 bot_app"""
    
    def __init__(self, user_client: TelegramClient):
        self.user_client: TelegramClient = user_client
        self.bot_app: Optional[Application] = None
        self._running = False
    
    async def initialize(self):
        """初始化 bot_app（user_client 已經透過構造函數注入）"""
        # Initialize PTB Bot Application
        if config.NOTIFIER_BOT_TOKEN:
            self.bot_app = Application.builder().token(config.NOTIFIER_BOT_TOKEN).build()
            self._register_handlers()
        else:
            print("⚠️ Notifier bot token not set, command handling will be disabled.")
            return False
        
        return True
    
    def _register_handlers(self):
        """註冊 bot 指令處理器"""
        if not self.bot_app:
            return
            
        # 創建帶有 bot_wrapper 參考的 command_handler 實例
        handler = command_handler.CommandHandler(self)
        
        # Register command handlers
        self.bot_app.add_handler(CommandHandler("done", handler.done_command))
        self.bot_app.add_handler(CommandHandler("tasks", handler.tasks_command))
        self.bot_app.add_handler(CommandHandler("completed", handler.completed_command))
        self.bot_app.add_handler(CommandHandler("help", handler.help_command))
        self.bot_app.add_handler(CommandHandler("userinfo", handler.user_info_command))  # 新增指令
        self.bot_app.add_handler(CommandHandler("send", handler.send_message_command))  # 新增指令
        # Add a handler for unknown commands
        self.bot_app.add_handler(MessageHandler(filters.COMMAND, handler.unknown_command))
    
    async def start(self):
        """啟動 bot_app（user_client 應該已經在外部啟動）"""
        if not self.user_client or not self.bot_app:
            raise ValueError("請先呼叫 initialize() 方法或確認 user_client 已注入")
        
        # Register Event Handlers for User Client
        user_handler = functools.partial(
            handle_message, 
            client=self.user_client, 
            bot=self.bot_app.bot
        )
        self.user_client.on(events.NewMessage())(user_handler)
        
        # Start bot application
        if self.bot_app and self.bot_app.updater:
            print("🚀 Notifier Bot is running...")
            # Initialize and start the bot application
            await self.bot_app.initialize()
            await self.bot_app.start()
            await self.bot_app.updater.start_polling()
            
            # Start scheduler with both clients
            scheduler_coro = run_scheduler(self.user_client, self.bot_app.bot)
            if scheduler_coro:
                asyncio.create_task(scheduler_coro)
        
        self._running = True
    
    async def run_until_disconnected(self):
        """運行直到斷線（user_client 由外部管理）"""
        if not self.user_client:
            return
            
        # user_client 的運行由外部控制，這裡只需要等待
        # 如果需要等待，可以使用一個簡單的等待邏輯
        while self._running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """停止 bot application（user_client 由外部管理）"""
        self._running = False
        
        # Stop bot application
        if self.bot_app and self.bot_app.updater:
            await self.bot_app.updater.stop()
            await self.bot_app.stop()
            await self.bot_app.shutdown()
        
        # user_client 的停止由外部處理
    
    # Bot 可以呼叫的 user_client 方法
    async def get_user_info(self, user_id: int):
        """透過 user_client 取得使用者資訊"""
        if not self.user_client:
            return None
        
        try:
            entity = await self.user_client.get_entity(user_id)
            return {
                'id': entity.id,
                'username': getattr(entity, 'username', None),
                'first_name': getattr(entity, 'first_name', None),
                'last_name': getattr(entity, 'last_name', None),
                'phone': getattr(entity, 'phone', None),
                'is_bot': getattr(entity, 'bot', False)
            }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
    
    async def send_message_as_user(self, chat_id: int, message: str):
        """透過 user_client 發送訊息"""
        if not self.user_client:
            return False
        
        try:
            await self.user_client.send_message(chat_id, message)
            return True
        except Exception as e:
            print(f"Error sending message as user: {e}")
            return False
    
    async def get_chat_info(self, chat_id: int):
        """透過 user_client 取得聊天室資訊"""
        if not self.user_client:
            return None
        
        try:
            entity = await self.user_client.get_entity(chat_id)
            return {
                'id': entity.id,
                'title': getattr(entity, 'title', None),
                'username': getattr(entity, 'username', None),
                'type': type(entity).__name__
            }
        except Exception as e:
            print(f"Error getting chat info: {e}")
            return None
    
    @property
    def is_running(self) -> bool:
        """檢查 bot 是否正在運行"""
        return self._running 