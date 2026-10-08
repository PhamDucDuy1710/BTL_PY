import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'attendance.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            class_id TEXT PRIMARY KEY,
            class_name TEXT NOT NULL
        )
    ''')

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            class_id TEXT,
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        )
    ''')

   
    cur.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            date_only TEXT,
            snapshot_path TEXT
        )
    ''')

   
    admin = cur.execute("SELECT * FROM admins WHERE username = 'admin'").fetchone()
    if not admin:
        default_hash = generate_password_hash("password")
        cur.execute("INSERT INTO admins (username, password) VALUES ('admin', ?)", (default_hash,))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()