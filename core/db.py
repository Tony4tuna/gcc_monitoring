# core/db.py
import os
import sqlite3
from pathlib import Path

# Always use the DB inside /data
BASE_DIR = Path(__file__).resolve().parents[1]           # .../gcc_monitoring
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def get_conn() -> sqlite3.Connection:
    """Open a connection to the app database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """
    Optional: call if you want to ensure tables exist.
    If your tables are already created by scripts, this can remain minimal.
    """
    # nothing required here for now (your scripts already create tables)
    # but keep it so app.py can import it safely.
    get_conn().close()
