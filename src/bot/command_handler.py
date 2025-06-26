import datetime
from telegram import Update
from telegram.ext import ContextTypes

from src.context import database
from src import config

async def _is_authorized(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the command is from an authorized chat."""
    if chat_id != config.NOTIFIER_TARGET_CHAT_ID:
        print(f"🚫 Ignored command from unauthorized chat ID: {chat_id}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, you are not authorized to use this bot."
        )
        return False
    return True

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Marks a task as done. Usage: /done <task_id>"""
    if not update.message or not update.effective_chat: return
    if not await _is_authorized(update.effective_chat.id, context):
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

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all pending tasks."""
    if not update.message or not update.effective_chat: return
    if not await _is_authorized(update.effective_chat.id, context):
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
        await update.message.reply_text(message, parse_mode='MarkdownV2')
        print(f"Sent pending tasks list with {len(pending_tasks)} tasks.")

    except Exception as e:
        await update.message.reply_text(f"取得任務列表時發生錯誤：{e}")
        print(f"🚨 ERROR processing /tasks command: {e}")

async def completed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists completed tasks. Usage: /completed [today|yesterday]"""
    if not update.message or not update.effective_chat: return
    if not await _is_authorized(update.effective_chat.id, context):
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the help message."""
    if not update.message or not update.effective_chat: return
    if not await _is_authorized(update.effective_chat.id, context):
        return
        
    help_message = (
        "👋 我是您的 AI Telegram 小助手！\n\n"
        "我能幫助您管理任務和提供每日摘要。以下是您可以使用的指令：\n\n"
        "`/tasks` \\- 顯示所有未處理的任務。\n"
        "`/completed` \\- 顯示所有已完成的任務。\n"
        "`/completed today` \\- 顯示今天完成的任務。\n"
        "`/completed yesterday` \\- 顯示昨天完成的任務。\n"
        "`/done <任務編號>` \\- 標記指定編號的任務為完成。\n\n"
        "我還會自動記錄您在群組中標記我 ( @您的使用者名稱 ) 或私訊我的任務喔！"
    )
    await update.message.reply_text(help_message, parse_mode='MarkdownV2')
    print("Sent help message.")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unknown commands."""
    if not update.message or not update.effective_chat: return
    if not await _is_authorized(update.effective_chat.id, context):
        return
    await update.message.reply_text("對不起，我不認得這個指令。請試試 /help 喔！") 