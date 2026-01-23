import sqlite3

conn = sqlite3.connect('data/app.db')

# Get table schema
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Logins'").fetchone()[0]

print("="*80)
print("LOGINS TABLE SCHEMA:")
print("="*80)
print(schema)
print("="*80)

conn.close()
