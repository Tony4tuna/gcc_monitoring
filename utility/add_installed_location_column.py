"""Add 'installed_location' TEXT column to Units if missing.
Run with the project's virtual environment:
    .venv\\Scripts\\python.exe utility\\add_installed_location_column.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from core.db import get_conn

def ensure_installed_location_column() -> bool:
    conn = get_conn()
    try:
        cur = conn.execute("PRAGMA table_info(Units)")
        cols = {row[1] for row in cur.fetchall()}  # row[1] = name
        if "installed_location" in cols:
            return False
        conn.execute("ALTER TABLE Units ADD COLUMN installed_location TEXT")
        conn.commit()
        return True
    finally:
        conn.close()

if __name__ == "__main__":
    changed = ensure_installed_location_column()
    if changed:
        print("Added installed_location column to Units")
    else:
        print("installed_location column already exists; no changes made")
