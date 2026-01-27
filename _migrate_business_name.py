import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")

conn = sqlite3.connect(str(DB_PATH))
conn.execute("PRAGMA foreign_keys = ON")

try:
    # Try to add the column
    conn.execute("ALTER TABLE PropertyLocations ADD COLUMN business_name TEXT DEFAULT ''")
    conn.commit()
    print("SUCCESS: Column 'business_name' added successfully")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("SUCCESS: Column 'business_name' already exists")
    else:
        print(f"ERROR: {e}")
        raise
finally:
    conn.close()

# Verify
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.execute("PRAGMA table_info(PropertyLocations)")
cols = [row[1] for row in cursor.fetchall()]
print(f"\nVERIFICATION: business_name in columns = {'business_name' in cols}")
conn.close()
