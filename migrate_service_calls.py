#!/usr/bin/env python3
"""
Migration script to add materials_services and labor_description columns to ServiceCalls table
"""

from core.db import get_conn

def migrate():
    conn = get_conn()
    try:
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(ServiceCalls)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "materials_services" not in columns:
            print("Adding materials_services column...")
            cursor.execute("ALTER TABLE ServiceCalls ADD COLUMN materials_services TEXT;")
            print("✓ materials_services column added")
        else:
            print("✓ materials_services column already exists")
        
        if "labor_description" not in columns:
            print("Adding labor_description column...")
            cursor.execute("ALTER TABLE ServiceCalls ADD COLUMN labor_description TEXT;")
            print("✓ labor_description column added")
        else:
            print("✓ labor_description column already exists")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
