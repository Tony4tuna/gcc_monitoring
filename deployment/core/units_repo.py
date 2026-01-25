# ---------------------------------------------------------
# Units Repository
# CRUD operations for HVAC equipment units
# ---------------------------------------------------------

from typing import List, Dict, Any, Optional
from core.db import get_conn


print(">>> LOADED units_repo.py FROM:", __file__)


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
