import sqlite3
from pathlib import Path

# This file is in the project root, so we can safely build the correct path
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "app.db"

print("Using DB:", DB_PATH)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("DROP TABLE IF EXISTS users;")

cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
""")

con.commit()
con.close()

print("users table rebuilt with password_hash ✅")
