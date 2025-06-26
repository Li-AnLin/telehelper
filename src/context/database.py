import sqlite3
import datetime
from src import config
from typing import Optional

def get_db_connection():
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the tasks table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            sender TEXT,
            content TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            tags TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")

async def add_task(task_data: dict):
    """Adds a new task to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (source, chat_id, message_id, sender, content, detected_at, completed_at, status, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task_data.get('source', 'telegram'),
        task_data.get('chat_id'),
        task_data.get('message_id'),
        task_data.get('sender'),
        task_data.get('content'),
        task_data.get('detected_at', datetime.datetime.now().isoformat()),
        task_data.get('completed_at', None),
        task_data.get('status', 'new'),
        ",".join(task_data.get('tags', []))
    ))
    conn.commit()
    conn.close()
    print(f"Task added from chat {task_data.get('chat_id')}")

async def get_pending_tasks():
    """Retrieves all tasks that are not marked as 'done'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE status != 'done'")
    tasks = cursor.fetchall()
    conn.close()
    return [dict(task) for task in tasks]

async def update_task_status(task_id: int, status: str):
    """Updates the status of a specific task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?", (status, datetime.datetime.now().isoformat(), task_id))
    conn.commit()
    conn.close()
    print(f"Task {task_id} status updated to {status}")

async def get_completed_tasks(from_date: Optional[str] = None, to_date: Optional[str] = None):
    """Retrieves all tasks that are marked as 'done', optionally filtered by date range."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tasks WHERE status = 'done'"
    params = []

    if from_date:
        query += " AND completed_at >= ?"
        params.append(from_date)
    if to_date:
        query += " AND completed_at <= ?"
        params.append(to_date)
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    return [dict(task) for task in tasks] 