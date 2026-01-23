import sqlite3

con = sqlite3.connect("gcc_monitoring.db")
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cur.fetchall()]

print("Tables in gcc_monitoring.db:")
for t in tables:
    print(" -", t)

con.close()
