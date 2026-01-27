from core.db import get_conn

conn = get_conn()
try:
    conn.execute("ALTER TABLE PropertyLocations ADD COLUMN business_name TEXT DEFAULT ''")
    conn.commit()
    print("✓ business_name column added")
except Exception as e:
    if "duplicate column name" in str(e).lower():
        print("✓ business_name column already exists")
    else:
        print(f"✗ Error: {e}")
finally:
    conn.close()
