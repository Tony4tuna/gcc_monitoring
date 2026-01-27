from core.db import get_conn

print("Testing row_factory with context manager:")
print('-' * 80)

# Test 1: Without context manager
conn = get_conn()
cursor = conn.execute('''
    SELECT 
        sc.ID,
        COALESCE(
            NULLIF(c.company, ''),
            NULLIF(TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')), ''),
            NULLIF(c.email, '')
        ) AS customer_name
    FROM ServiceCalls sc
    LEFT JOIN Customers c ON sc.customer_id = c.ID
    ORDER BY sc.ID DESC LIMIT 2
''')
rows = cursor.fetchall()
print("Without context manager:")
for row in rows:
    d = dict(row)
    print(f"  Ticket #{d['ID']}: customer_name = {d.get('customer_name')}")
conn.close()

print()

# Test 2: With context manager
with get_conn() as conn:
    cursor = conn.execute('''
        SELECT 
            sc.ID,
            COALESCE(
                NULLIF(c.company, ''),
                NULLIF(TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')), ''),
                NULLIF(c.email, '')
            ) AS customer_name
        FROM ServiceCalls sc
        LEFT JOIN Customers c ON sc.customer_id = c.ID
        ORDER BY sc.ID DESC LIMIT 2
    ''')
    rows = cursor.fetchall()
    print("With context manager:")
    for row in rows:
        d = dict(row)
        print(f"  Ticket #{d['ID']}: customer_name = {d.get('customer_name')}")
