import sqlite3


def open_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        group_name TEXT,
                        is_admin INTEGER,
                        name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_name TEXT,
                        subject TEXT,
                        notification_text TEXT,
                        deadline TEXT)''')
    conn.commit()
    return conn, cursor


def close_db(conn):
    conn.close()
