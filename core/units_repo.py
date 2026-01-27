# ---------------------------------------------------------
# Units Repository
# CRUD operations for HVAC equipment units
# ---------------------------------------------------------

from typing import List, Dict, Any, Optional
from core.db import get_conn


print(">>> LOADED units_repo.py FROM:", __file__)


# ---------------------------------------------------------
# TICKET UNIT HELPERS (junction table)
# ---------------------------------------------------------

def get_ticket_unit_ids(ticket_id: int) -> List[int]:
    """Return list of unit_ids linked to a ticket via TicketUnits, fallback to ServiceCalls.unit_id."""
    with get_conn() as conn:
        rows = conn.execute("SELECT unit_id FROM TicketUnits WHERE ticket_id = ? ORDER BY sequence_order", (ticket_id,)).fetchall()
        ids = [int(r[0]) for r in rows]
        if ids:
            return ids
        # fallback to ServiceCalls.unit_id
        row = conn.execute("SELECT unit_id FROM ServiceCalls WHERE ID = ?", (ticket_id,)).fetchone()
        return [int(row[0])] if row and row[0] is not None else []


def set_ticket_units(ticket_id: int, unit_ids: List[int]) -> None:
    """Replace TicketUnits entries for a ticket (keeps order)."""
    unit_ids = [int(u) for u in unit_ids if u is not None]
    with get_conn() as conn:
        conn.execute("DELETE FROM TicketUnits WHERE ticket_id = ?", (ticket_id,))
        for idx, unit_id in enumerate(unit_ids):
            conn.execute(
                "INSERT INTO TicketUnits (ticket_id, unit_id, sequence_order) VALUES (?, ?, ?)",
                (ticket_id, unit_id, idx)
            )
        conn.commit()


# ---------------------------------------------------------
# LIST UNITS (used by Equipment page)
# ---------------------------------------------------------

def list_units(search: str = "", location_id: Optional[int] = None) -> List[Dict[str, Any]]:
    query = """
    SELECT *
    FROM Units
    WHERE 1=1
    """
    params = []

    if location_id:
        query += " AND location_id = ?"
        params.append(location_id)

    if search:
        query += """
        AND (
            unit_tag LIKE ?
            OR make LIKE ?
            OR model LIKE ?
            OR serial LIKE ?
        )
        """
        s = f"%{search}%"
        params.extend([s, s, s, s])

    query += " ORDER BY unit_id"

    with get_conn() as conn:
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------
# GET SINGLE UNIT BY ID (🔥 REQUIRED BY ISSUE DIALOG)
# ---------------------------------------------------------

def get_unit_by_id(unit_id: int) -> Optional[Dict[str, Any]]:
    """
    Return a single unit by unit_id.
    Used by Unit Issue Dialog.
    """
    query = """
    SELECT *
    FROM Units
    WHERE unit_id = ?
    """
    with get_conn() as conn:
        cursor = conn.execute(query, (unit_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------
# CREATE UNIT
# ---------------------------------------------------------

def create_unit(data: Dict[str, Any]) -> int:
    query = """
    INSERT INTO Units (
        location_id,
        unit_tag,
        equipment_type,
        make,
        model,
        serial,
        refrigerant_type,
        voltage,
        amperage,
        btu_rating,
        tonnage,
        breaker_size,
        inst_date,
        warranty_end_date,
        note_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        data.get("location_id"),
        data.get("unit_tag"),
        data.get("equipment_type"),
        data.get("make"),
        data.get("model"),
        data.get("serial"),
        data.get("refrigerant_type"),
        data.get("voltage"),
        data.get("amperage"),
        data.get("btu_rating"),
        data.get("tonnage"),
        data.get("breaker_size"),
        data.get("inst_date"),
        data.get("warranty_end_date"),
        data.get("note_id"),
    )

    with get_conn() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


# ---------------------------------------------------------
# UPDATE UNIT
# ---------------------------------------------------------

def update_unit(unit_id: int, data: Dict[str, Any]) -> bool:
    fields = []
    params = []

    allowed_fields = [
        "location_id",
        "unit_tag",
        "equipment_type",
        "make",
        "model",
        "serial",
        "refrigerant_type",
        "voltage",
        "amperage",
        "btu_rating",
        "tonnage",
        "breaker_size",
        "inst_date",
        "warranty_end_date",
        "note_id",
    ]

    for field in allowed_fields:
        if field in data:
            fields.append(f"{field} = ?")
            params.append(data[field])

    if not fields:
        return False

    query = f"UPDATE Units SET {', '.join(fields)} WHERE unit_id = ?"
    params.append(unit_id)

    with get_conn() as conn:
        cursor = conn.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------
# DELETE UNIT
# ---------------------------------------------------------

def delete_unit(unit_id: int) -> bool:
    query = "DELETE FROM Units WHERE unit_id = ?"
    with get_conn() as conn:
        cursor = conn.execute(query, (unit_id,))
        conn.commit()
        return cursor.rowcount > 0
