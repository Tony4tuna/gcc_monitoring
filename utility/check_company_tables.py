import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import get_conn


def main() -> None:
    conn = get_conn()
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Company%'").fetchall()
    print("Tables:", tables)
    for tbl in ("CompanyProfile", "CompanyInfo"):
        try:
            cols = cur.execute(f"PRAGMA table_info({tbl})").fetchall()
            print(f"\n{tbl} columns ({len(cols)}):")
            for cid, name, ctype, notnull, default, pk in cols:
                print(f"  - {name} ({ctype})")
        except Exception as e:
            print(f"\n{tbl} error: {e}")
    conn.close()


if __name__ == "__main__":
    main()
