# --------------------------
# tickets_repo.py
# --------------------------

##print(">>> LOADED tickets_repo.py FROM:", __file__)

"""
Service Calls Repository
CRUD operations for service call management
(uses existing ServiceCalls table)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from core.db import get_conn


# -------------------------------------------------
# CORE CRUD (USED BY EXISTING PAGES)
# -------------------------------------------------

def create_service_call(data: Dict[str, Any]) -> int:
    query = """
    INSERT INTO ServiceCalls (
        customer_id, location_id, unit_id,
        title, description, priority, status,
        requested_by_login_id,
        materials_services, labor_description,
        created
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """
    params = (
        data.get("customer_id"),
        data.get("location_id"),
        data.get("unit_id"),
        data.get("title"),
        data.get("description"),
        data.get("priority", "Normal"),
        data.get("status", "Open"),
        data.get("requested_by_login_id"),
        data.get("materials_services"),
        data.get("labor_description"),
    )

    with get_conn() as conn:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid


def get_service_call(call_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM ServiceCalls WHERE ID = ?"
    with get_conn() as conn:
        row = conn.execute(query, (call_id,)).fetchone()
        return dict(row) if row else None




#---------------------------------
#  List_service_calls
#---------------------------------
def list_service_calls(
    customer_id: Optional[int] = None,
    location_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List service calls with optional filters"""

    query = """
    SELECT 
        sc.*,
        COALESCE(
            NULLIF(c.company, ''),
            NULLIF(TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')), ''),
            NULLIF(c.email, '')
        ) AS customer_name,
        COALESCE(NULLIF(p.address1, ''), NULLIF(p.address2, '')) as location_address,
        u.unit_tag as unit_name
    FROM ServiceCalls sc
    LEFT JOIN Customers c ON sc.customer_id = c.ID
    LEFT JOIN PropertyLocations p ON sc.location_id = p.ID
    LEFT JOIN Units u ON sc.unit_id = u.unit_id
    WHERE 1=1
    """
    params = []

    if customer_id:
        query += " AND sc.customer_id = ?"
        params.append(customer_id)

    if location_id:
        query += " AND sc.location_id = ?"
        params.append(location_id)

    if status:
        query += " AND sc.status = ?"
        params.append(status)

    if priority:
        query += " AND sc.priority = ?"
        params.append(priority)

    query += " ORDER BY sc.created DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn() as conn:
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

#----------------------------------------




def update_service_call(call_id: int, data: Dict[str, Any]) -> bool:
    fields = []
    params = []

    for k, v in data.items():
        fields.append(f"{k} = ?")
        params.append(v)

    if not fields:
        return False

    query = f"UPDATE ServiceCalls SET {', '.join(fields)} WHERE ID = ?"
    params.append(call_id)

    with get_conn() as conn:
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return cur.rowcount > 0


def delete_service_call(call_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM ServiceCalls WHERE ID = ?", (call_id,))
        conn.commit()
        return cur.rowcount > 0


# -------------------------------------------------
# DUPLICATE / TIME RULE HELPERS
# -------------------------------------------------

def get_recent_calls_for_unit(unit_id: int, customer_id: int, hours: int = 24):
    query = """
    SELECT *
    FROM ServiceCalls
    WHERE unit_id = ?
      AND customer_id = ?
      AND created >= datetime('now', ?)
    """
    with get_conn() as conn:
        rows = conn.execute(
            query, (unit_id, customer_id, f"-{hours} hours")
        ).fetchall()
        return [dict(r) for r in rows]


def get_last_ticket_time_for_unit(unit_id: int):
    query = """
    SELECT MAX(created) AS last_created
    FROM ServiceCalls
    WHERE unit_id = ?
    """
    with get_conn() as conn:
        row = conn.execute(query, (unit_id,)).fetchone()
        return row["last_created"] if row else None


# -------------------------------------------------
# ISSUE → TICKET HELPERS (USED BY DIALOG)
# -------------------------------------------------

def get_open_ticket_for_issue(issue_id: int):
    query = """
    SELECT *
    FROM ServiceCalls
    WHERE issue_id = ?
      AND status IN ('Open', 'In Progress')
    LIMIT 1
    """
    with get_conn() as conn:
        row = conn.execute(query, (issue_id,)).fetchone()
        return dict(row) if row else None


def create_ticket(data: Dict[str, Any]) -> int:
    """
    Wrapper used by Unit Issue Dialog.
    """
    return create_service_call(data)


def get_service_call_stats(customer_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Return basic statistics for service calls.
    Used by pages/tickets.py.
    """
    where = ""
    params = []

    if customer_id:
        where = "WHERE customer_id = ?"
        params.append(customer_id)

    query = f"""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open,
        SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
        SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) AS closed
    FROM ServiceCalls
    {where}
    """

    with get_conn() as conn:
        row = conn.execute(query, tuple(params)).fetchone()
        return dict(row) if row else {
            "total": 0,
            "open": 0,
            "in_progress": 0,
            "closed": 0,
        }

def search_service_calls(search: str, customer_id: Optional[int] = None):
    """
    Search service calls by ticket ID, title, or description.
    Used by pages/tickets.py.
    """
    query = """
    SELECT
        sc.*,
        COALESCE(
            NULLIF(c.company, ''),
            NULLIF(TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')), ''),
            NULLIF(c.email, '')
        ) AS customer_name,
        COALESCE(NULLIF(p.address1, ''), NULLIF(p.address2, '')) AS location_address,
        u.unit_tag AS unit_name
    FROM ServiceCalls sc
    LEFT JOIN Customers c ON sc.customer_id = c.ID
    LEFT JOIN PropertyLocations p ON sc.location_id = p.ID
    LEFT JOIN Units u ON sc.unit_id = u.unit_id
    WHERE (
        CAST(sc.ID AS TEXT) LIKE ?
        OR sc.title LIKE ?
        OR sc.description LIKE ?
    )
    """
    params = [f"%{search}%", f"%{search}%", f"%{search}%"]

    if customer_id:
        query += " AND sc.customer_id = ?"
        params.append(customer_id)

    query += " ORDER BY sc.created DESC LIMIT 50"

    with get_conn() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
