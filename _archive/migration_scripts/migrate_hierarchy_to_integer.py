import sqlite3
import shutil
from datetime import datetime

# Backup the database first
backup_name = f'data/app.db.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"Creating backup: {backup_name}")
shutil.copy2('data/app.db', backup_name)
print("✅ Backup created\n")

conn = sqlite3.connect('data/app.db')

print("="*80)
print("MIGRATING HIERARCHY COLUMN FROM TEXT TO INTEGER")
print("="*80)

# Step 1: Create new table with INTEGER hierarchy
print("\nStep 1: Creating new Logins table with INTEGER hierarchy...")
conn.execute("""
CREATE TABLE Logins_new (
  ID              INTEGER PRIMARY KEY AUTOINCREMENT,
  login_id        TEXT NOT NULL UNIQUE,
  password_hash   TEXT NOT NULL,
  password_salt   TEXT NOT NULL,
  hierarchy       INTEGER NOT NULL,                    -- Changed from TEXT to INTEGER
  customer_id     INTEGER,
  location_id     INTEGER,
  is_active       INTEGER DEFAULT 1,
  created         TEXT DEFAULT (datetime('now')),
  last_login      TEXT,
  FOREIGN KEY(customer_id) REFERENCES Customers(ID) ON DELETE SET NULL,
  FOREIGN KEY(location_id) REFERENCES PropertyLocations(ID) ON DELETE SET NULL
)
""")
print("✅ New table created")

# Step 2: Copy data with hierarchy conversion
print("\nStep 2: Copying data with hierarchy conversion...")

hierarchy_map = {
    '1': 1, 'GOD': 1,
    '2': 2, 'admin': 2, 'administrator': 2,
    '3': 3, 'Tech_GCC': 3, 'tech_gcc': 3,
    '4': 4, 'client': 4,
    '5': 5, 'client_mngs': 5,
}

old_rows = conn.execute("SELECT * FROM Logins ORDER BY ID").fetchall()

for row in old_rows:
    user_id, login_id, password_hash, password_salt, hierarchy_text, customer_id, location_id, is_active, created, last_login = row
    
    # Convert hierarchy to integer
    if hierarchy_text.isdigit():
        hierarchy_int = int(hierarchy_text)
    elif hierarchy_text in hierarchy_map:
        hierarchy_int = hierarchy_map[hierarchy_text]
    else:
        print(f"  ⚠️  WARNING: Unknown hierarchy '{hierarchy_text}' for {login_id}, defaulting to 5")
        hierarchy_int = 5
    
    conn.execute("""
        INSERT INTO Logins_new (ID, login_id, password_hash, password_salt, hierarchy, customer_id, location_id, is_active, created, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, login_id, password_hash, password_salt, hierarchy_int, customer_id, location_id, is_active, created, last_login))
    
    print(f"  ✅ Migrated ID {user_id}: {login_id:<30} hierarchy={hierarchy_text} → {hierarchy_int}")

print(f"✅ Migrated {len(old_rows)} users")

# Step 3: Drop old table and rename new table
print("\nStep 3: Replacing old table with new table...")
conn.execute("DROP TABLE Logins")
conn.execute("ALTER TABLE Logins_new RENAME TO Logins")
print("✅ Table replaced")

conn.commit()

# Step 4: Verify
print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)

# Check schema
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Logins'").fetchone()[0]
print("\nNew schema:")
print(schema)

# Check data
print("\nData verification:")
rows = conn.execute("""
SELECT ID, login_id, hierarchy, typeof(hierarchy) AS type,
    CASE 
        WHEN hierarchy = 1 THEN 'GOD'
        WHEN hierarchy = 2 THEN 'Administrator'
        WHEN hierarchy = 3 THEN 'Tech_GCC'
        WHEN hierarchy = 4 THEN 'Client'
        WHEN hierarchy = 5 THEN 'Client_Mngs'
        ELSE 'UNKNOWN'
    END AS label
FROM Logins ORDER BY hierarchy, ID
""").fetchall()

print(f"\n{'ID':<5} {'Login':<30} {'Hierarchy':<12} {'Type':<10} {'Label':<15}")
print("-" * 80)
for row in rows:
    print(f"{row[0]:<5} {row[1]:<30} {row[2]:<12} {row[3]:<10} {row[4]:<15}")

# Final check
all_integer = all(row[3] == 'integer' for row in rows)
all_valid = all(row[2] in (1, 2, 3, 4, 5) for row in rows)

print("\n" + "="*80)
if all_integer and all_valid:
    print("✅ SUCCESS: Migration complete! All hierarchy values are now integers (1-5)")
    print(f"✅ Backup saved to: {backup_name}")
else:
    print("⚠️  WARNING: Some hierarchy values are still invalid")
print("="*80 + "\n")

conn.close()
