import datetime
from telegram import Update
from telegram.ext import ContextTypes
from typing import TYPE_CHECKING

from src.context import database
from src import config

if TYPE_CHECKING:
    from src.bot.bot_wrapper import TelegramBotWrapper


class CommandHandler:
    """處理 Telegram Bot 指令的類別"""
    
    def __init__(self, bot_wrapper: 'TelegramBotWrapper'):
        self.bot_wrapper = bot_wrapper
    
    async def _is_authorized(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Checks if the command is from an authorized chat."""
        if chat_id != config.NOTIFIER_TARGET_CHAT_ID:
            print(f"🚫 Ignored command from unauthorized chat ID: {chat_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, you are not authorized to use this bot."
            )
            return False
        return True

    async def done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Marks a task as done. Usage: /done <task_id>"""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return

        try:
            # context.args contains a list of strings, the arguments passed with the command
            if not context.args:
                raise IndexError("Command requires an argument.")
            task_id = int(context.args[0])
            await database.update_task_status(task_id, "done")
            await update.message.reply_text(f"✅ 任務 {task_id} 已標記為完成！")
            print(f"Task {task_id} marked as done via bot command.")
        except (ValueError, IndexError):
            await update.message.reply_text("請提供有效的任務編號，例如：`/done 123`")
        except Exception as e:
            await update.message.reply_text(f"更新任務時發生錯誤：{e}")
            print(f"🚨 ERROR processing /done command: {e}")

    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Lists all pending tasks."""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return
            
        print("Processing /tasks command...")
        try:
            pending_tasks = await database.get_pending_tasks()
            if not pending_tasks:
                await update.message.reply_text("🎉 目前沒有未處理事項！")
                return
            
            message = "📜 **目前未處理事項**：\n\n"
            for i, task in enumerate(pending_tasks, 1):
                chat_info = f"來自: {task['sender']}"
                status_icon = "🔴" if task['status'] == 'new' else "🟡"
                message += f"{i}. (ID: {task['id']}) {status_icon} [{chat_info}] {task['content'][:50]}...\n"
            
            message += "\n使用 `/done <任務編號>` 來標記完成。"
            await update.message.reply_text(message, parse_mode='Markdown')
            print(f"Sent pending tasks list with {len(pending_tasks)} tasks.")

        except Exception as e:
            await update.message.reply_text(f"取得任務列表時發生錯誤：{e}")
            print(f"🚨 ERROR processing /tasks command: {e}")

    async def completed_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Lists completed tasks. Usage: /completed [today|yesterday]"""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return

        print("Processing /completed command...")
        from_date = None
        to_date = None

        if context.args:
            time_frame = context.args[0].lower()
            today = datetime.date.today()
            if time_frame == "today":
                from_date = today.isoformat()
                to_date = today.isoformat() + "T23:59:59.999999"
            elif time_frame == "yesterday":
                yesterday = today - datetime.timedelta(days=1)
                from_date = yesterday.isoformat()
                to_date = yesterday.isoformat() + "T23:59:59.999999"
            else:
                await update.message.reply_text("無效的參數。請使用 `/completed today` 或 `/completed yesterday` 或不帶參數。")
                return

        try:
            completed_tasks = await database.get_completed_tasks(from_date=from_date, to_date=to_date)
            if not completed_tasks:
                if from_date and to_date:
                    await update.message.reply_text(f"🎉 在 {from_date.split('T')[0]} 沒有已完成事項！")
                else:
                    await update.message.reply_text("🎉 目前沒有已完成事項！")
                return
            
            message_title = "✅ **已完成事項**"
            if from_date and to_date:
                if from_date.split('T')[0] == datetime.date.today().isoformat():
                    message_title += " (今天)"
                elif from_date.split('T')[0] == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
                    message_title += " (昨天)"
                else:
                    message_title += f" ({from_date.split('T')[0]} 至 {to_date.split('T')[0]})"

            message = f"{message_title}：\n\n"

            for i, task in enumerate(completed_tasks, 1):
                chat_info = f"對話 ID: {task['chat_id']}"
                message += f"{i}. (ID: {task['id']}) [{chat_info}] {task['content'][:50]}... (於 {task['completed_at'].split('T')[0]} 完成)\n"
            
            await update.message.reply_text(message, parse_mode='MarkdownV2')
            print(f"Sent completed tasks list with {len(completed_tasks)} tasks.")

        except Exception as e:
            await update.message.reply_text(f"取得已完成任務列表時發生錯誤：{e}")
            print(f"🚨 ERROR processing /completed command: {e}")

    async def user_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """取得使用者資訊（示範 bot 呼叫 user_client 功能）. Usage: /userinfo <user_id>"""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return

        try:
            if not context.args:
                await update.message.reply_text("請提供使用者 ID，例如：`/userinfo 123456789`")
                return
            
            user_id = int(context.args[0])
            print(f"Processing /userinfo command for user ID: {user_id}")
            
            # 使用 bot_wrapper 來呼叫 user_client 功能
            user_info = await self.bot_wrapper.get_user_info(user_id)
            
            if not user_info:
                await update.message.reply_text(f"❌ 無法取得使用者 ID {user_id} 的資訊")
                return
            
            message = f"👤 **使用者資訊**：\n\n"
            message += f"ID: `{user_info['id']}`\n"
            if user_info['username']:
                message += f"使用者名稱: @{user_info['username']}\n"
            if user_info['first_name']:
                message += f"名字: {user_info['first_name']}\n"
            if user_info['last_name']:
                message += f"姓氏: {user_info['last_name']}\n"
            if user_info['phone']:
                message += f"電話: {user_info['phone']}\n"
            message += f"是否為機器人: {'是' if user_info['is_bot'] else '否'}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            print(f"Sent user info for user ID: {user_id}")

        except ValueError:
            await update.message.reply_text("請提供有效的使用者 ID 數字")
        except Exception as e:
            await update.message.reply_text(f"取得使用者資訊時發生錯誤：{e}")
            print(f"🚨 ERROR processing /userinfo command: {e}")

    async def send_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """透過 user_client 發送訊息. Usage: /send <chat_id> <message>"""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return

        try:
            if not context.args or len(context.args) < 2:
                await update.message.reply_text("請提供聊天室 ID 和訊息，例如：`/send 123456789 你好！`")
                return
            
            chat_id = int(context.args[0])
            message_text = " ".join(context.args[1:])
            
            print(f"Processing /send command to chat ID: {chat_id}")
            
            # 使用 bot_wrapper 來透過 user_client 發送訊息
            success = await self.bot_wrapper.send_message_as_user(chat_id, message_text)
            
            if success:
                await update.message.reply_text(f"✅ 訊息已透過 User Client 發送到聊天室 {chat_id}")
                print(f"Message sent to chat {chat_id} via user client")
            else:
                await update.message.reply_text(f"❌ 無法發送訊息到聊天室 {chat_id}")

        except ValueError:
            await update.message.reply_text("請提供有效的聊天室 ID 數字")
        except Exception as e:
            await update.message.reply_text(f"發送訊息時發生錯誤：{e}")
            print(f"🚨 ERROR processing /send command: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Displays the help message."""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return
            
        help_message = (
            "👋 我是您的 AI Telegram 小助手！\n\n"
            "我能幫助您管理任務和提供每日摘要。以下是您可以使用的指令：\n\n"
            "📋 **任務管理**：\n"
            "`/tasks` - 顯示所有未處理的任務。\n"
            "`/completed` - 顯示所有已完成的任務。\n"
            "`/completed today` - 顯示今天完成的任務。\n"
            "`/completed yesterday` - 顯示昨天完成的任務。\n"
            "`/done <任務編號>` - 標記指定編號的任務為完成。\n\n"
            "🔧 **User Client 功能**：\n"
            "`/userinfo <使用者ID>` - 取得使用者資訊（透過 User Client）。\n"
            "`/send <聊天室ID> <訊息>` - 透過 User Client 發送訊息。\n\n"
            "我還會自動記錄您在群組中標記我 ( @您的使用者名稱 ) 或私訊我的任務喔！"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
        print("Sent help message.")

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles unknown commands."""
        if not update.message or not update.effective_chat: return
        if not await self._is_authorized(update.effective_chat.id, context):
            return
        await update.message.reply_text("對不起，我不認得這個指令。請試試 /help 喔！")


# 為了向後兼容，保留原始函數（如果有其他地方在使用）
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated: 請使用 CommandHandler 類別"""
    print("⚠️ Warning: Using deprecated done_command function")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated: 請使用 CommandHandler 類別"""
    print("⚠️ Warning: Using deprecated tasks_command function")

async def completed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated: 請使用 CommandHandler 類別"""
    print("⚠️ Warning: Using deprecated completed_command function")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated: 請使用 CommandHandler 類別"""
    print("⚠️ Warning: Using deprecated help_command function")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deprecated: 請使用 CommandHandler 類別"""
    print("⚠️ Warning: Using deprecated unknown_command function") 