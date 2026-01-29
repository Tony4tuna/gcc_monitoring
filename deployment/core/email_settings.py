# core/email_settings.py
# Centralized SMTP settings loader for the app.
# Ensures EmailSettings table exists AND required columns exist (including smtp_pass).

from __future__ import annotations

from typing import Dict, Any

from core.db import get_conn


def _table_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {r["name"] for r in rows} if rows else set()


def ensure_email_settings_table() -> None:
    """Create EmailSettings table if missing and ensure required columns exist."""
    conn = get_conn()
    try:
        # Create table if it doesn't exist (includes smtp_pass)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS EmailSettings (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          smtp_host TEXT,
          smtp_port INTEGER DEFAULT 2525,
          use_tls INTEGER DEFAULT 1,
          smtp_user TEXT,
          smtp_pass TEXT,
          smtp_from TEXT
        )
        """)
        conn.execute("INSERT OR IGNORE INTO EmailSettings (id, smtp_port, use_tls) VALUES (1, 2525, 1)")
        conn.commit()

        # If table existed before, make sure smtp_pass exists
        cols = _table_columns(conn, "EmailSettings")
        if "smtp_pass" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_pass TEXT")
        if "smtp_from" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_from TEXT")
        if "use_tls" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN use_tls INTEGER DEFAULT 1")
        if "smtp_port" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_port INTEGER DEFAULT 2525")
        if "smtp_host" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_host TEXT")
        if "smtp_user" not in cols:
            conn.execute("ALTER TABLE EmailSettings ADD COLUMN smtp_user TEXT")

        conn.commit()
    finally:
        conn.close()


def get_email_settings() -> Dict[str, Any]:
    """Returns the single EmailSettings row (id=1)."""
    ensure_email_settings_table()
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM EmailSettings WHERE id=1").fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def update_email_settings(payload: Dict[str, Any]) -> None:
    """Update the EmailSettings row (id=1)."""
    ensure_email_settings_table()
    conn = get_conn()
    try:
        conn.execute("""
        UPDATE EmailSettings
        SET smtp_host=?,
            smtp_port=?,
            use_tls=?,
            smtp_user=?,
            smtp_pass=?,
            smtp_from=?
        WHERE id=1
        """, (
            (payload.get("smtp_host") or "").strip(),
            int(payload.get("smtp_port") or 2525),
            1 if payload.get("use_tls") else 0,
            (payload.get("smtp_user") or "").strip(),
            (payload.get("smtp_pass") or "").strip(),
            (payload.get("smtp_from") or "").strip(),
        ))
        conn.commit()
    finally:
        conn.close()
