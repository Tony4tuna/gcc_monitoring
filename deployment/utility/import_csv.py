import csv
import sys
from pathlib import Path

# Use project root data directory and app database via core.db
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Ensure project root on sys.path so `core` package imports work
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "data"

from core.db import get_conn
CUSTOMERS_CSV = DATA_DIR / "Customers.csv"
LOCATIONS_CSV = DATA_DIR / "PropertyLocations.csv"


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(v):
    return str(v).strip() if v is not None else ""


def main():
    con = get_conn()
    cur = con.cursor()

    # -------------------------
    # 1) IMPORT CUSTOMERS
    # -------------------------
    customers = read_csv(CUSTOMERS_CSV)
    for r in customers:
        cur.execute("""
            INSERT OR IGNORE INTO Customers
            (ID, company, first_name, last_name, email, phone1, phone2,
             address1, address2, city, state, zip, notes, idstring, csr, referral,
             credit_status, website, mobile, fax, extension1, extension2, flag_and_lock, created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(r["ID"]),
            norm(r.get("Company")),
            norm(r.get("First Name")),
            norm(r.get("Last Name")),
            norm(r.get("Email")),
            norm(r.get("Phone 1")),
            norm(r.get("Phone 2")),
            norm(r.get("Address 1")),
            norm(r.get("Address 2")),
            norm(r.get("City")),
            norm(r.get("State")),
            norm(r.get("Zip")),
            norm(r.get("Notes")),
            norm(r.get("IDstring")),
            norm(r.get("CSR")),
            norm(r.get("Referral")),
            norm(r.get("Credit Status")),
            norm(r.get("Website")),
            norm(r.get("Mobile")),
            norm(r.get("Fax")),
            norm(r.get("Extension1")),
            norm(r.get("Extension2")),
            int(norm(r.get("FlagAndLock") or "0") or 0),
            norm(r.get("Created")),
        ))

    print(f"Customers imported: {len(customers)}")

    # Build Customers.IDstring -> Customers.ID map
    customer_map = {
        row["idstring"]: row["ID"]
        for row in cur.execute("SELECT ID, idstring FROM Customers")
        if row["idstring"]
    }

    # -------------------------
    # 2) IMPORT LOCATIONS
    # -------------------------
    locations = read_csv(LOCATIONS_CSV)

    imported = 0
    skipped = 0

    for r in locations:
        custid = norm(r.get("CustID"))
        customer_id = customer_map.get(custid)

        if not customer_id:
            skipped += 1
            continue

        cur.execute("""
            INSERT OR IGNORE INTO PropertyLocations
            (ID, customer_id, custid, address1, address2, city, state, zip,
             contact, job_phone, job_phone2, notes, extended_notes,
             residential, commercial, date_created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(r["ID"]),
            customer_id,
            custid,
            norm(r.get("Address 1")),
            norm(r.get("Address 2")),
            norm(r.get("City")),
            norm(r.get("State")),
            norm(r.get("Zip")),
            norm(r.get("Contact")),
            norm(r.get("Job Phone")),
            norm(r.get("Job Phone 2")),
            norm(r.get("Notes")),
            norm(r.get("ExtendedNotes")),
            int(norm(r.get("Residential") or "0") or 0),
            int(norm(r.get("Commercial") or "0") or 0),
            norm(r.get("Date Created")),
        ))
        imported += 1

    print(f"Locations imported: {imported}")
    if skipped:
        print(f"⚠ Locations skipped (no matching Customers.IDstring for CustID): {skipped}")

    con.commit()
    con.close()

    print("IMPORT COMPLETE ✅ (Customers + Locations)")


if __name__ == "__main__":
    main()
