import sqlite3

conn = sqlite3.connect('data/app.db')
conn.row_factory = sqlite3.Row

query = """
SELECT 
    ID, login_id, hierarchy,
    typeof(hierarchy) AS hierarchy_type,
    CASE 
        WHEN hierarchy = 1 THEN 'GOD'
        WHEN hierarchy = 2 THEN 'Administrator'
        WHEN hierarchy = 3 THEN 'Tech_GCC'
        WHEN hierarchy = 4 THEN 'Client'
        WHEN hierarchy = 5 THEN 'Client_Mngs'
        ELSE 'UNKNOWN'
    END AS hierarchy_label
FROM Logins
ORDER BY hierarchy
"""

rows = conn.execute(query).fetchall()

print(f"\n{'='*85}")
print(f"HIERARCHY VERIFICATION RESULTS - Found {len(rows)} users")
print(f"{'='*85}\n")

print(f"{'ID':<5} {'Login':<30} {'Hierarchy':<12} {'Type':<10} {'Label':<15}")
print("-" * 85)

for r in rows:
    print(f"{r['ID']:<5} {r['login_id']:<30} {r['hierarchy']:<12} {r['hierarchy_type']:<10} {r['hierarchy_label']:<15}")

print(f"\n{'='*85}")

# Check for any issues
non_integer_count = sum(1 for r in rows if r['hierarchy_type'] != 'integer')
invalid_value_count = sum(1 for r in rows if r['hierarchy'] not in (1, 2, 3, 4, 5))

if non_integer_count > 0:
    print(f"⚠️  WARNING: {non_integer_count} users have non-integer hierarchy values!")
elif invalid_value_count > 0:
    print(f"⚠️  WARNING: {invalid_value_count} users have invalid hierarchy values (not 1-5)!")
else:
    print("✅ SUCCESS: All hierarchy values are valid integers (1-5)")

print(f"{'='*85}\n")

conn.close()
