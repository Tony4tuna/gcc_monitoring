"""
Create UnitSetpoints table if it doesn't exist
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import get_conn

def create_setpoints_table():
    """Create UnitSetpoints table"""
    conn = get_conn()
    try:
        # Create table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS UnitSetpoints (
              id              INTEGER PRIMARY KEY AUTOINCREMENT,
              unit_id         INTEGER NOT NULL,
              mode            TEXT,
              cooling_setpoint REAL,
              heating_setpoint REAL,
              deadband        REAL,
              
              schedule_enabled INTEGER DEFAULT 0,
              schedule_day    TEXT,
              schedule_start_time TEXT,
              schedule_end_time   TEXT,
              schedule_mode   TEXT,
              schedule_temp   REAL,
              
              updated         TEXT DEFAULT (datetime('now')),
              updated_by_login_id INTEGER,
              FOREIGN KEY(unit_id) REFERENCES Units(unit_id) ON DELETE CASCADE,
              FOREIGN KEY(updated_by_login_id) REFERENCES Logins(ID) ON DELETE SET NULL
            )
        """)
        
        # Create index
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_unitsetpoints_unit_id ON UnitSetpoints(unit_id)
        """)
        
        conn.commit()
        print("✓ UnitSetpoints table created successfully")
        
        # Verify
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='UnitSetpoints'").fetchone()
        if result:
            print("✓ Table verified in database")
        else:
            print("✗ Table verification failed")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_setpoints_table()
