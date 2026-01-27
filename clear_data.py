"""
Clear all data from database while preserving schema
Run this before hardware testing to start fresh
"""
from core.db import get_conn

def clear_all_data():
    """Delete only telemetry and service data, preserve customers/locations/units"""
    with get_conn() as conn:
        # Disable foreign keys temporarily
        conn.execute("PRAGMA foreign_keys = OFF")
        
        # Clear only operational/telemetry data (keep customers, locations)
        tables_to_clear = [
            "UnitReadings",      # Telemetry data
            "ServiceCalls",      # Service tickets
            "Units",             # Equipment units
        ]
        
        for table in tables_to_clear:
            try:
                conn.execute(f"DELETE FROM {table}")
                print(f"✓ Cleared {table}")
            except Exception as e:
                print(f"⚠ Could not clear {table}: {e}")
        
        # Re-enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        
        print("\n✅ Telemetry, service data & units cleared")
        print("✅ Customers & Locations preserved - ready for hardware testing")

if __name__ == "__main__":
    confirm = input("This will DELETE ALL DATA. Type 'YES' to confirm: ")
    if confirm == "YES":
        clear_all_data()
    else:
        print("Cancelled")
