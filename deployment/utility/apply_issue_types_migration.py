#!/usr/bin/env python3
"""
Migration: Create issue_types table (also known as Symptoms)
Run this script to update the database with the new issue_types/Symptoms table.
"""

import sqlite3
import sys
from pathlib import Path

# Get the project root (parent of utility folder)
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "app.db"

def apply_migration():
    """Apply the issue_types/Symptoms table migration."""
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        print("🔄 Applying issue_types migration...")
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create issue_types table (Symptoms)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issue_types (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                code            TEXT NOT NULL UNIQUE,
                title           TEXT NOT NULL,
                description     TEXT,
                category        TEXT,
                severity_default TEXT DEFAULT 'Normal',
                active          INTEGER DEFAULT 1,
                display_order   INTEGER DEFAULT 0,
                created         TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_types_active ON issue_types(active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_types_category ON issue_types(category)")
        
        # Add symptom_id to ServiceCalls if not already present
        cursor.execute("PRAGMA table_info(ServiceCalls)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'symptom_id' not in columns:
            cursor.execute("""
                ALTER TABLE ServiceCalls ADD COLUMN symptom_id INTEGER REFERENCES issue_types(id)
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_servicecalls_symptom ON ServiceCalls(symptom_id)")
            print("✅ Added symptom_id column to ServiceCalls")
        
        # Insert default issue types if table is empty
        cursor.execute("SELECT COUNT(*) FROM issue_types")
        if cursor.fetchone()[0] == 0:
            default_issues = [
                ('NOT_COOLING', 'Not cooling properly', 'The unit is running but the space is not getting cool enough', 'Cooling', 'High', 1),
                ('NOT_HEATING', 'Not heating properly', 'The unit is running but the space is not getting warm enough', 'Heating', 'High', 2),
                ('NO_POWER', 'Unit not turning on', 'The unit does not start or respond when turned on', 'Power', 'Critical', 3),
                ('NOISE', 'Making unusual noise', 'The unit is making loud, strange, or grinding noises', 'Noise', 'Medium', 4),
                ('LEAK', 'Water leaking', 'Water is dripping or pooling around the unit', 'Leak', 'High', 5),
                ('ICE', 'Ice forming on unit', 'Ice or frost is visible on the unit or lines', 'Cooling', 'High', 6),
                ('SMELL', 'Bad smell or odor', 'The unit is producing an unusual or unpleasant odor', 'Air Quality', 'Medium', 7),
                ('TOO_COLD', 'Space too cold', 'The temperature is lower than desired even at higher settings', 'Cooling', 'Medium', 8),
                ('TOO_HOT', 'Space too hot', 'The temperature is higher than desired even at lower settings', 'Heating', 'Medium', 9),
                ('SHORT_CYCLE', 'Turns on and off frequently', 'The unit starts and stops repeatedly in short cycles', 'Operation', 'Medium', 10),
                ('NO_AIR', 'No air flow', 'Little or no air is coming from the vents', 'Air Flow', 'High', 11),
                ('OTHER', 'Other issue', 'Issue not listed above - will describe in notes', 'Other', 'Low', 99),
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO issue_types (code, title, description, category, severity_default, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, default_issues)
            print(f"✅ Inserted {len(default_issues)} default issue types")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Migration complete! Database: {DB_PATH}")
        return True
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
