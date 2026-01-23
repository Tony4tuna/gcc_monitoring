import sqlite3

conn = sqlite3.connect('data/app.db')

print("="*80)
print("FIXING HIERARCHY COLUMN - Converting text to integer")
print("="*80)

# Step 1: Check current data
cursor = conn.execute("SELECT ID, login_id, hierarchy, typeof(hierarchy) FROM Logins ORDER BY ID")
rows = cursor.fetchall()

print(f"\nBefore fix - Found {len(rows)} users:")
for row in rows:
    print(f"  ID {row[0]}: {row[1]:<30} hierarchy={row[2]:<10} type={row[3]}")

# Step 2: Map text values to integers
hierarchy_map = {
    '1': 1, 'GOD': 1,
    '2': 2, 'admin': 2, 'administrator': 2,
    '3': 3, 'Tech_GCC': 3, 'tech_gcc': 3,
    '4': 4, 'client': 4,
    '5': 5, 'client_mngs': 5,
}

# Step 3: Update each row
print("\nUpdating rows...")
for row in rows:
    user_id = row[0]
    login_id = row[1]
    current_hierarchy = str(row[2])
    
    # Try to convert to integer
    if current_hierarchy.isdigit():
        new_hierarchy = int(current_hierarchy)
    elif current_hierarchy in hierarchy_map:
        new_hierarchy = hierarchy_map[current_hierarchy]
    else:
        print(f"  ⚠️  WARNING: Unknown hierarchy '{current_hierarchy}' for {login_id}, defaulting to 5")
        new_hierarchy = 5
    
    conn.execute("UPDATE Logins SET hierarchy = ? WHERE ID = ?", (new_hierarchy, user_id))
    print(f"  ✅ Updated ID {user_id}: {login_id:<30} {current_hierarchy} → {new_hierarchy}")

conn.commit()

# Step 4: Verify fix
print("\n" + "="*80)
print("VERIFICATION - After fix:")
print("="*80)

cursor = conn.execute("""
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
""")

rows = cursor.fetchall()

print(f"\n{'ID':<5} {'Login':<30} {'Hierarchy':<12} {'Type':<10} {'Label':<15}")
print("-" * 80)
for row in rows:
    print(f"{row[0]:<5} {row[1]:<30} {row[2]:<12} {row[3]:<10} {row[4]:<15}")

# Check success
all_integer = all(row[3] == 'integer' for row in rows)
all_valid = all(row[2] in (1, 2, 3, 4, 5) for row in rows)

print("\n" + "="*80)
if all_integer and all_valid:
    print("✅ SUCCESS: All hierarchy values are now valid integers (1-5)")
else:
    print("⚠️  WARNING: Some hierarchy values are still invalid")
print("="*80 + "\n")

conn.close()
