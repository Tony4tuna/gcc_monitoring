from core.db import get_conn

conn = get_conn()
tables = ['Customers', 'PropertyLocations', 'Units', 'EmployeeProfile']

for t in tables:
    try:
        cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
        date_cols = [r[1] for r in cols if 'created' in r[1].lower() or 'date' in r[1].lower()]
        print(f"{t}: {date_cols}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")

conn.close()
