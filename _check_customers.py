from core.db import get_conn

conn = get_conn()
cursor = conn.execute('''
    SELECT sc.ID, sc.customer_id, c.company, c.first_name, c.last_name, c.email 
    FROM ServiceCalls sc 
    LEFT JOIN Customers c ON sc.customer_id = c.ID 
    ORDER BY sc.ID DESC LIMIT 3
''')
rows = cursor.fetchall()
print('Ticket | Customer ID | Company          | Name                 | Email')
print('-' * 80)
for r in rows:
    tid = r[0] or 0
    cid = r[1] or 0
    company = (r[2] or '')[:15]
    name = f"{r[3] or ''} {r[4] or ''}".strip()[:20]
    email = r[5] or ''
    print(f'{tid:6} | {cid:11} | {company:15} | {name:20} | {email}')
conn.close()
