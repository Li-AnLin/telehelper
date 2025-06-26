import datetime
from telethon import events
from src.context import database
from src import config

async def handle_bot_command(event: events.NewMessage.Event):
    """Handles commands sent to the bot, like /done"""
    
    # Security check: Only process messages from the target chat ID
    if event.chat_id != config.NOTIFIER_TARGET_CHAT_ID:
        print(f"🚫 Ignored command from unauthorized chat ID: {event.chat_id}")
        return

    text = event.message.message.lower()
    command_parts = text.split(" ")
    command = command_parts[0]
    
    if command == "/done":
        try:
            # Assumes the format is /done <task_id>
            task_id = int(command_parts[1])
            await database.update_task_status(task_id, "done")
            await event.reply(f"✅ 任務 {task_id} 已標記為完成！")
            print(f"Task {task_id} marked as done via bot command.")
        except (ValueError, IndexError):
            await event.reply("請提供有效的任務編號，例如：`/done 123`")
        except Exception as e:
            await event.reply(f"更新任務時發生錯誤：{e}")
            print(f"🚨 ERROR processing /done command: {e}")

    elif command == "/tasks":
        print("Processing /tasks command...")
        try:
            pending_tasks = await database.get_pending_tasks()
            if not pending_tasks:
                await event.reply("🎉 目前沒有未處理事項！")
                return
            
            message = "📜 **目前未處理事項**：\n\n"
            for i, task in enumerate(pending_tasks, 1):
                # For commands, we don't have access to the main client for chat titles
                # So we'll display chat_id for now, or you can enhance this with chat caching
                chat_info = f"來自: {task['sender']}"

                # Use status to assign an icon
                status_icon = "🔴" if task['status'] == 'new' else "🟡"
                message += f"{i}. (ID: {task['id']}) {status_icon} [{chat_info}] {task['content'][:50]}...\n"
            
            message += "\n使用 `/done <任務編號>` 來標記完成。"
            await event.reply(message, parse_mode='md')
            print(f"Sent pending tasks list with {len(pending_tasks)} tasks.")

        except Exception as e:
            await event.reply(f"取得任務列表時發生錯誤：{e}")
            print(f"🚨 ERROR processing /tasks command: {e}")

    elif command == "/completed":
        print("Processing /completed command...")
        from_date = None
        to_date = None

        if len(command_parts) > 1:
            time_frame = command_parts[1]
            today = datetime.date.today()
            if time_frame == "today":
                from_date = today.isoformat()
                to_date = today.isoformat() + "T23:59:59.999999" # Include entire day
            elif time_frame == "yesterday":
                yesterday = today - datetime.timedelta(days=1)
                from_date = yesterday.isoformat()
                to_date = yesterday.isoformat() + "T23:59:59.999999" # Include entire day
            else:
                await event.reply("無效的參數。請使用 `/completed today` 或 `/completed yesterday` 或不帶參數。")
                return

        try:
            completed_tasks = await database.get_completed_tasks(from_date=from_date, to_date=to_date)
            if not completed_tasks:
                if from_date and to_date:
                    await event.reply(f"🎉 在 {from_date.split('T')[0]} 沒有已完成事項！")
                else:
                    await event.reply("🎉 目前沒有已完成事項！")
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
            
            await event.reply(message, parse_mode='md')
            print(f"Sent completed tasks list with {len(completed_tasks)} tasks.")

        except Exception as e:
            await event.reply(f"取得已完成任務列表時發生錯誤：{e}")
            print(f"🚨 ERROR processing /completed command: {e}")

    elif command == "/help":
        help_message = (
            "👋 我是您的 AI Telegram 小助手！\n\n"
            "我能幫助您管理任務和提供每日摘要。以下是您可以使用的指令：\n\n"
            "`/tasks` - 顯示所有未處理的任務。\n"
            "`/completed` - 顯示所有已完成的任務。\n"
            "`/completed today` - 顯示今天完成的任務。\n"
            "`/completed yesterday` - 顯示昨天完成的任務。\n"
            "`/done <任務編號>` - 標記指定編號的任務為完成。\n\n"
            "我還會自動記錄您在群組中標記我 ( `@您的使用者名稱` ) 或私訊我的任務喔！"
        )
        await event.reply(help_message, parse_mode='md')
        print("Sent help message.")

    # You can add more commands here with elif
    # elif text.startswith("/help"):
    #     await event.reply("I can help you manage tasks. Use /done <id> to complete a task.") 