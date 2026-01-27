# core/locations_repo.py
from typing import Any, Dict, List, Optional
from core.db import get_conn


def _dicts(rows):
    return [dict(r) for r in rows]


def list_locations(search: str = "", customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
    search = (search or "").strip()
    like = f"%{search}%"

    sql = """
    SELECT
        ID,
        custid,
        address1,
        address2,
        city,
        state,
        zip,
        contact,
        job_phone,
        job_phone2,
        notes,
        extendednotes,
        residential,
        commercial,
        business_name,
        date_created
    FROM PropertyLocations
    WHERE 1=1
    """
    params = []

    if customer_id is not None:
        sql += " AND customer_id = ?"
        params.append(customer_id)

    if search:
        sql += """
        AND (
            address1 LIKE ?
            OR address2 LIKE ?
            OR city LIKE ?
            OR state LIKE ?
            OR zip LIKE ?
            OR contact LIKE ?
            OR job_phone LIKE ?
            OR job_phone2 LIKE ?
            OR notes LIKE ?
            OR extendednotes LIKE ?
        )
        """
        params += [like] * 10

    sql += " ORDER BY ID DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return _dicts(rows)


def get_location(location_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM PropertyLocations WHERE ID = ?", (location_id,)).fetchone()
        return dict(row) if row else None


def create_location(data: Dict[str, Any]) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO PropertyLocations (
                customer_id, custid,
                address1, address2, city, state, zip,
                contact, job_phone, job_phone2,
                notes, extendednotes,
                residential, commercial, business_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(data["custid"]),
                str(data.get("custid", "")),
                data.get("address1", "").strip(),
                data.get("address2", "").strip(),
                data.get("city", "").strip(),
                data.get("state", "").strip(),
                data.get("zip", "").strip(),
                data.get("contact", "").strip(),
                data.get("job_phone", "").strip(),
                data.get("job_phone2", "").strip(),
                data.get("notes", "").strip(),
                data.get("extendednotes", "").strip(),
                int(data.get("residential", 0)),
                int(data.get("commercial", 0)),
                data.get("business_name", "").strip(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def update_location(location_id: int, data: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE PropertyLocations SET
                customer_id = ?, custid = ?,
                address1 = ?, address2 = ?, city = ?, state = ?, zip = ?,
                contact = ?, job_phone = ?, job_phone2 = ?,
                notes = ?, extendednotes = ?,
                residential = ?, commercial = ?, business_name = ?
            WHERE ID = ?
            """,
            (
                int(data["custid"]),
                str(data.get("custid", "")),
                data.get("address1", "").strip(),
                data.get("address2", "").strip(),
                data.get("city", "").strip(),
                data.get("state", "").strip(),
                data.get("zip", "").strip(),
                data.get("contact", "").strip(),
                data.get("job_phone", "").strip(),
                data.get("job_phone2", "").strip(),
                data.get("notes", "").strip(),
                data.get("extendednotes", "").strip(),
                int(data.get("residential", 0)),
                int(data.get("commercial", 0)),
                data.get("business_name", "").strip(),
                location_id,
            ),
        )
        conn.commit()


def delete_location(location_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM PropertyLocations WHERE ID = ?", (location_id,))
        conn.commit()


def get_location_by_id(location_id: int):
    """
    Return a single location by ID.
    Used by Unit Issue Dialog.
    """
    query = """
    SELECT *
    FROM PropertyLocations
    WHERE ID = ?
    """
    from core.db import get_conn

    with get_conn() as conn:
        cursor = conn.execute(query, (location_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
