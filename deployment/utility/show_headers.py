import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

files = ["Customers.csv", "PropertyLocations.csv", "Equipment.csv"]

for name in files:
    p = DATA_DIR / name
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
    print("\n" + name)
    for h in headers:
        print(" -", h)
