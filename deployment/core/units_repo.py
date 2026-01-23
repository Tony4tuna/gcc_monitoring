# core/units_repo.py
# Repo with unit_id auto-generated, unit_tag added

from typing import Any, Dict, List, Optional
from core.db import get_conn

def _dicts(rows):
    return [dict(r) for r in rows]

def list_units(search: str = "", location_id: Optional[int] = None) -> List[Dict[str, Any]]:
    search = (search or "").strip()
    like = f"%{search}%"
    sql = """
    SELECT unit_id, unit_tag, location_id, make, model, serial, note_id, inst_date, 
           equipment_type, refrigerant_type, voltage, amperage, btu_rating, tonnage, 
           breaker_size, warranty_end_date, created
    FROM Units
    WHERE 1=1
    """
    params = []
    if location_id is not None:
        sql += " AND location_id = ?"
        params.append(location_id)
    if search:
        sql += """
        AND (make LIKE ? OR model LIKE ? OR serial LIKE ? OR unit_tag LIKE ?
             OR CAST(unit_id AS TEXT) LIKE ?)
        """
        params.extend([like] * 5)
    sql += " ORDER BY unit_id DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return _dicts(rows)

def create_unit(data: Dict[str, Any]) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO Units (location_id, make, model, serial, note_id, inst_date, unit_tag,
                             equipment_type, refrigerant_type, voltage, amperage, btu_rating, 
                             tonnage, breaker_size, warranty_end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(data["location_id"]),
                data.get("make", "").strip(),
                data.get("model", "").strip(),
                data.get("serial", "").strip(),
                data.get("note_id"),
                data.get("inst_date", "").strip(),
                data.get("unit_tag", "").strip(),
                data.get("equipment_type", "RTU").strip(),
                data.get("refrigerant_type", "").strip(),
                data.get("voltage", "").strip(),
                data.get("amperage", "").strip(),
                data.get("btu_rating", "").strip(),
                data.get("tonnage", "").strip(),
                data.get("breaker_size", "").strip(),
                data.get("warranty_end_date", "").strip(),
            ),
        )
        conn.commit()
        return cur.lastrowid  # auto-generated unit_id

def update_unit(unit_id: int, data: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE Units SET
                location_id = ?,
                make = ?,
                model = ?,
                serial = ?,
                note_id = ?,
                inst_date = ?,
                unit_tag = ?,
                equipment_type = ?,
                refrigerant_type = ?,
                voltage = ?,
                amperage = ?,
                btu_rating = ?,
                tonnage = ?,
                breaker_size = ?,
                warranty_end_date = ?
            WHERE unit_id = ?
            """,
            (
                int(data["location_id"]),
                data.get("make", "").strip(),
                data.get("model", "").strip(),
                data.get("serial", "").strip(),
                data.get("note_id"),
                data.get("inst_date", "").strip(),
                data.get("unit_tag", "").strip(),
                data.get("equipment_type", "RTU").strip(),
                data.get("refrigerant_type", "").strip(),
                data.get("voltage", "").strip(),
                data.get("amperage", "").strip(),
                data.get("btu_rating", "").strip(),
                data.get("tonnage", "").strip(),
                data.get("breaker_size", "").strip(),
                data.get("warranty_end_date", "").strip(),
                int(unit_id),
            ),
        )
        conn.commit()

def delete_unit(unit_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM Units WHERE unit_id = ?", (unit_id,))
        conn.commit()