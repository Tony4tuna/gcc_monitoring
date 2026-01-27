from __future__ import annotations

from typing import Dict
from .db import get_conn


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _count(conn, table_name: str) -> int:
    # table name is controlled by our code (not user input), so this is safe here
    row = conn.execute(f'SELECT COUNT(*) AS c FROM "{table_name}"').fetchone()
    return int(row["c"]) if row and "c" in row.keys() else int(row[0])


def get_summary_counts() -> Dict[str, int]:
    """
    Returns counts for dashboard tiles.
    Supports either your HVAC schema (Customers, PropertyLocations, equipments)
    or future tables (clients, locations, equipment).
    """
    with get_conn() as conn:
        # Pick the best matching table names for the current DB
        clients_table = "Customers" if _table_exists(conn, "Customers") else (
            "clients" if _table_exists(conn, "clients") else None
        )

        locations_table = "PropertyLocations" if _table_exists(conn, "PropertyLocations") else (
            "locations" if _table_exists(conn, "locations") else None
        )

        # Equipment table: prefer HVAC schema 'Units', fallback to generic names
        equipment_table = "Units" if _table_exists(conn, "Units") else (
            "equipments" if _table_exists(conn, "equipments") else (
                "equipment" if _table_exists(conn, "equipment") else None
            )
        )

        return {
            "clients": _count(conn, clients_table) if clients_table else 0,
            "locations": _count(conn, locations_table) if locations_table else 0,
            "equipment": _count(conn, equipment_table) if equipment_table else 0,
        }
