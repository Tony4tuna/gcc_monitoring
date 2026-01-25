import sys
from pathlib import Path
import csv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import get_conn

DATA_DIR = PROJECT_ROOT / "data"
EQUIP_CSV = DATA_DIR / "Equipment.csv"
MAP_CSV = DATA_DIR / "LocationIdMap.csv"
TEMPLATE_CSV = DATA_DIR / "LocationIdMap.template.csv"


def load_location_map():
    mapping = {}
    if MAP_CSV.exists():
        with MAP_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ext = (r.get("ExternalLocationID") or "").strip()
                pid = (r.get("PropertyLocationID") or "").strip()
                if ext and pid:
                    mapping[ext] = int(pid)
    return mapping


def generate_template(external_ids):
    # Write a template mapping CSV listing all external Location_IDs
    with TEMPLATE_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ExternalLocationID", "PropertyLocationID"]) 
        for ext in sorted(external_ids):
            w.writerow([ext, ""])  # empty PropertyLocationID for user to fill
    print(f"⚠ Wrote mapping template: {TEMPLATE_CSV}")


def main():
    if not EQUIP_CSV.exists():
        print("✗ Equipment.csv not found in data/")
        return

    # Collect distinct external Location_IDs and import using provided map
    external_ids = set()
    rows = []
    with EQUIP_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        # Skip first junk line if present
        first = f.readline()
        reader = csv.DictReader(f)
        for r in reader:
            loc_id = (r.get("Location_ID") or "").strip()
            if loc_id:
                external_ids.add(loc_id)
            rows.append(r)

    mapping = load_location_map()
    if not mapping:
        print("⚠ No LocationIdMap.csv provided; generating template from Equipment.csv IDs...")
        generate_template(external_ids)
        print("Please fill PropertyLocationID values (matching PropertyLocations.ID) and rerun.")
        return

    conn = get_conn()
    cur = conn.cursor()

    imported = 0
    skipped = 0
    unmapped = set()

    # Optional: prepare Notes insertion when present
    for r in rows:
        loc_id = (r.get("Location_ID") or "").strip()
        make = (r.get("Make") or "").strip()
        model = (r.get("Model") or "").strip()
        serial = (r.get("Serial") or "").strip()
        note = (r.get("Note") or "").strip()
        inst_date = (r.get("Date") or "").strip()

        prop_location_id = mapping.get(loc_id)
        if not prop_location_id:
            unmapped.add(loc_id)
            skipped += 1
            continue

        note_id = None
        if note:
            cur.execute("INSERT INTO Notes (title, body) VALUES (?, ?)", ("Equipment Note", note))
            note_id = cur.lastrowid

        # De-dup: skip if a unit already exists for same location/model/serial
        existing = cur.execute(
            "SELECT unit_id FROM Units WHERE location_id=? AND model=? AND serial=?",
            (prop_location_id, model, serial)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO Units (unit_id, location_id, make, model, serial, note_id, inst_date)
            VALUES (NULL, ?, ?, ?, ?, ?, ?)
            """,
            (prop_location_id, make, model, serial, note_id, inst_date),
        )
        imported += 1

    conn.commit()
    conn.close()

    print("EQUIPMENT IMPORT (MAPPING) COMPLETE ✅")
    print(f"Imported units: {imported}")
    print(f"Skipped (no mapping or duplicate): {skipped}")
    if unmapped:
        print(f"Unmapped Location_IDs ({len(unmapped)}): sample -> {sorted(list(unmapped))[:10]}")


if __name__ == "__main__":
    main()
