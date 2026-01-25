"""Add fan column to UnitSetpoints table"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_conn

def add_fan_column():
    conn = get_conn()
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(UnitSetpoints)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'fan' in columns:
            print("✓ Fan column already exists")
        else:
            conn.execute('ALTER TABLE UnitSetpoints ADD COLUMN fan TEXT DEFAULT "Auto"')
            conn.commit()
            print("✓ Added fan column to UnitSetpoints")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_fan_column()
