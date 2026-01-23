import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("gcc_monitoring.db")
CSV_PATH = Path("data") / "Equipment.csv"


def norm(v):
    return str(v).strip() if v is not None else ""


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Build map: PropertyLocations.CustID -> PropertyLocations.ID
    loc_map = {
        norm(row["custid"]): int(row["ID"])
        for row in cur.execute("SELECT ID, custid FROM PropertyLocations")
        if row["custid"]
    }

    imported = 0
    skipped = 0

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        # Skip the first junk row: ,,,,,
        first_line = f.readline()

        reader = csv.DictReader(f)  # starts at real header line
        for r in reader:
            custid = norm(r.get("Location_ID"))
            location_id = loc_map.get(custid)

            if not location_id:
                skipped += 1
                continue

            make = norm(r.get("Make"))
            model = norm(r.get("Model"))
            serial = norm(r.get("Serial"))
            note = norm(r.get("Note"))
            inst_date = norm(r.get("Date"))

            # Units schema:
            # unit_id (INTEGER PRIMARY KEY) -> insert NULL to auto-generate
            # location_id (required)
            # make, model, serial, note_id (optional), inst_date
            #
            # We'll store Note text into Notes table if present,
            # then reference note_id. If empty, note_id stays NULL.

            note_id = None
            if note:
                cur.execute("INSERT INTO Notes (title, body) VALUES (?, ?)", ("Equipment Note", note))
                note_id = cur.lastrowid

            cur.execute("""
                INSERT INTO Units (unit_id, location_id, make, model, serial, note_id, inst_date)
                VALUES (NULL, ?, ?, ?, ?, ?, ?)
            """, (location_id, make, model, serial, note_id, inst_date))

            imported += 1

    con.commit()

    total_units = cur.execute("SELECT COUNT(*) AS n FROM Units").fetchone()["n"]
    con.close()

    print("EQUIPMENT IMPORT COMPLETE ✅")
    print(f"Imported units: {imported}")
    if skipped:
        print(f"⚠ Skipped rows (no matching PropertyLocations.CustID): {skipped}")
    print(f"Total Units in DB now: {total_units}")


if __name__ == "__main__":
    main()
