"""Add thermostat_name column to UnitSetpoints table"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_conn

def add_name_column():
    conn = get_conn()
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(UnitSetpoints)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'thermostat_name' in columns:
            print("✓ Thermostat name column already exists")
        else:
            conn.execute('ALTER TABLE UnitSetpoints ADD COLUMN thermostat_name TEXT')
            conn.commit()
            print("✓ Added thermostat_name column to UnitSetpoints")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_name_column()
