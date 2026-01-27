from core.db import get_conn

conn = get_conn()

# Direct query using same COALESCE logic
cursor = conn.execute('''
    SELECT 
        sc.ID,
        c.company,
        LENGTH(c.company) as company_len,
        c.first_name,
        c.last_name,
        c.email,
        COALESCE(
            NULLIF(c.company, ''),
            NULLIF(TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')), ''),
            NULLIF(c.email, '')
        ) AS customer_name
    FROM ServiceCalls sc
    LEFT JOIN Customers c ON sc.customer_id = c.ID
    ORDER BY sc.ID DESC LIMIT 3
''')

rows = cursor.fetchall()
print('Ticket | Company | Len | First | Last | Email | customer_name')
print('-' * 90)
for r in rows:
    print(f'{r[0]:6} | {str(r[1])[:15]:15} | {r[2] or 0:3} | {str(r[3])[:10]:10} | {str(r[4])[:10]:10} | {str(r[5])[:20]:20} | {r[6]}')

conn.close()
