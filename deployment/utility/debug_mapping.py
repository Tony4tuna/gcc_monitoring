import sqlite3, csv

con = sqlite3.connect("gcc_monitoring.db")
cur = con.cursor()

print("\n--- Sample Customers ---")
for r in cur.execute("SELECT ID, idstring FROM Customers LIMIT 10"):
    print(r)

print("\n--- Sample PropertyLocations ---")
for r in cur.execute("SELECT ID, customer_id, custid FROM PropertyLocations LIMIT 10"):
    print(r)

print("\n--- Sample Equipment Location_ID ---")
with open("data/Equipment.csv", "r", encoding="utf-8-sig") as f:
    f.readline()  # skip junk row
    reader = csv.DictReader(f)
    vals = []
    for i, row in enumerate(reader):
        vals.append(row["Location_ID"])
        if i >= 10:
            break
print(vals)

con.close()
