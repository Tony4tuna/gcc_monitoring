import sys
from pathlib import Path
import csv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import get_conn

def main():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Customers WHERE idstring IS NOT NULL AND idstring != ''")
    customers_with_idstring = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT idstring) FROM Customers WHERE idstring IS NOT NULL AND idstring != ''")
    distinct_customer_idstrings = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM PropertyLocations WHERE custid IS NOT NULL AND custid != ''")
    locations_with_custid = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT custid) FROM PropertyLocations WHERE custid IS NOT NULL AND custid != ''")
    distinct_location_custids = cur.fetchone()[0]

    # Build sets for intersection
    cur.execute("SELECT DISTINCT idstring FROM Customers WHERE idstring IS NOT NULL AND idstring != ''")
    customer_ids = {row[0] for row in cur.fetchall()}
    cur.execute("SELECT DISTINCT custid FROM PropertyLocations WHERE custid IS NOT NULL AND custid != ''")
    location_custids = {row[0] for row in cur.fetchall()}

    intersection = customer_ids & location_custids

    # Check Equipment.csv Location_ID distinct values
    csv_path = PROJECT_ROOT / "data" / "Equipment.csv"
    equip_location_ids = set()
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                v = (r.get("Location_ID") or "").strip()
                if v:
                    equip_location_ids.add(v)

    print("MAPPING REPORT ✅")
    print(f"Customers with idstring: {customers_with_idstring} (distinct: {distinct_customer_idstrings})")
    print(f"Locations with custid: {locations_with_custid} (distinct: {distinct_location_custids})")
    print(f"Customer↔Location intersection: {len(intersection)}")
    if equip_location_ids:
        print(f"Equipment CSV distinct Location_IDs: {len(equip_location_ids)}")
        overlap = len(equip_location_ids & location_custids)
        print(f"Equipment Location_ID ↔ Location custid overlap: {overlap}")
    else:
        print("Equipment.csv not found or no Location_IDs")

    conn.close()

if __name__ == "__main__":
    main()
