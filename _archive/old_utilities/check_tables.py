import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "app.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"Database: {DB_PATH}")
print("Existing tables:")
for table in tables:
    print(f"  - {table}")

conn.close()
