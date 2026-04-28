import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("Database/attendance.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        date TEXT,
        time TEXT,
        UNIQUE(user_id, date)
    )
    """)

    conn.commit()
    conn.close()

def insert_user(user_id, username):
    conn = sqlite3.connect("Database/attendance.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    if cursor.fetchone():
        print("User already exists")
    else:
        cursor.execute(
            "INSERT INTO users (id, username) VALUES (?, ?)",
            (user_id, username)
        )
        conn.commit()

    conn.close()

def already_marked(user_id):
    conn = sqlite3.connect("Database/attendance.db")
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT 1 FROM attendance WHERE user_id=? AND date=?",
        (user_id, today)
    )

    result = cursor.fetchone()
    conn.close()

    return result is not None


def mark_db_attendance(user_id):
    conn = sqlite3.connect("Database/attendance.db")
    cursor = conn.cursor()

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    cursor.execute(
        "INSERT INTO attendance (user_id, date, time) VALUES (?, ?, ?)",
        (user_id, date, time)
    )

    conn.commit()
    conn.close()

def get_attendance_by_date(date):
    conn = sqlite3.connect("Database/attendance.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT users.username, attendance.user_id, attendance.time
        FROM attendance
        JOIN users ON users.id = attendance.user_id
        WHERE attendance.date = ?
    """, (date,))

    records = cursor.fetchall()
    conn.close()

    return records