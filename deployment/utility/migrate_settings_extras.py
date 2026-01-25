import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

COMPANYINFO_COLUMNS = {
    "fax": "ALTER TABLE CompanyInfo ADD COLUMN fax TEXT",
    "logo_path": "ALTER TABLE CompanyInfo ADD COLUMN logo_path TEXT",
}

EMPLOYEE_COLUMNS = {
    "can_login": "ALTER TABLE EmployeeProfile ADD COLUMN can_login INTEGER DEFAULT 0",
    "mfa_enabled": "ALTER TABLE EmployeeProfile ADD COLUMN mfa_enabled INTEGER DEFAULT 0",
    "security_clearance": "ALTER TABLE EmployeeProfile ADD COLUMN security_clearance TEXT",
    "access_scope": "ALTER TABLE EmployeeProfile ADD COLUMN access_scope TEXT",
    "password_last_reset": "ALTER TABLE EmployeeProfile ADD COLUMN password_last_reset TEXT",
}


def ensure_columns(table: str, mapping: dict, conn: sqlite3.Connection) -> None:
    existing = {c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for col, stmt in mapping.items():
        if col not in existing:
            conn.execute(stmt)
            print(f"Added column {col} to {table}")
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_columns("CompanyInfo", COMPANYINFO_COLUMNS, conn)
    ensure_columns("EmployeeProfile", EMPLOYEE_COLUMNS, conn)
    print("CompanyInfo columns:", [c[1] for c in conn.execute("PRAGMA table_info(CompanyInfo)").fetchall()])
    print("EmployeeProfile columns:", [c[1] for c in conn.execute("PRAGMA table_info(EmployeeProfile)").fetchall()])
    conn.close()


if __name__ == "__main__":
    main()
