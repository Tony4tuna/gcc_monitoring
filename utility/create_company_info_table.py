"""Ensure legacy settings tables exist (CompanyInfo and EmailSettings)."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

COMPANYINFO_SCHEMA = """
CREATE TABLE IF NOT EXISTS CompanyInfo (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    company_name TEXT,
    name TEXT,
    address1 TEXT,
    address2 TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,
    phone TEXT,
    fax TEXT,
    email TEXT,
    service_email TEXT,
    website TEXT,
    business_license TEXT,
    logo_path TEXT,
    owner_email TEXT,
    updated TEXT DEFAULT (datetime('now'))
);
"""

EMAIL_SCHEMA = """
CREATE TABLE IF NOT EXISTS EmailSettings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    smtp_host TEXT,
    smtp_port INTEGER DEFAULT 587,
    use_tls INTEGER DEFAULT 1,
    smtp_user TEXT,
    smtp_pass TEXT,
    smtp_from TEXT,
    updated TEXT DEFAULT (datetime('now'))
);
"""


def main():
        conn = sqlite3.connect(DB_PATH)
        try:
                conn.execute(COMPANYINFO_SCHEMA)
                conn.execute(EMAIL_SCHEMA)
                conn.execute("INSERT OR IGNORE INTO EmailSettings (id, smtp_port, use_tls) VALUES (1, 587, 1)")
                conn.commit()
                print("✓ CompanyInfo table ensured")
                print("✓ EmailSettings table ensured")
        finally:
                conn.close()


if __name__ == "__main__":
    main()
