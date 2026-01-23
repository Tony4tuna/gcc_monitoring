"""
Service Calls Repository
CRUD operations for service call management (uses existing ServiceCalls table)
"""

from typing import List, Dict, Any, Optional
from core.db import get_conn
from datetime import datetime


def generate_ticket_number(prefix: str = "SC") -> str:
    """Generate unique ticket number"""
    now = datetime.now()
    year = now.strftime("%Y")
    
    # Get last ID to generate sequence
    with get_conn() as conn:
        cursor = conn.execute("SELECT MAX(ID) as max_id FROM ServiceCalls")
        result = cursor.fetchone()
        
        if result and result["max_id"]:
            seq = result["max_id"] + 1
        else:
            seq = 1
    
    return f"{prefix}-{year}-{seq:05d}"


def create_service_call(data: Dict[str, Any]) -> int:
    """Create new service call"""
    
    query = """
    INSERT INTO ServiceCalls (
        customer_id, location_id, unit_id,
        title, description, priority, status,
        requested_by_login_id, materials_services, labor_description, created
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
        data.get("labor_description")
    )
    
    with get_conn() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def get_service_call(call_id: int) -> Optional[Dict[str, Any]]:
    """Get single service call by ID"""
    query = """
    SELECT 
        sc.*,
        c.company as customer_name,
        c.email as customer_email,
        c.phone1 as customer_phone,
        p.address1 as location_address,
        p.city as location_city,
        p.state as location_state,
        u.serial as unit_serial,
        u.unit_tag as unit_name,
        u.equipment_type,
        u.refrigerant_type,
        u.voltage,
        u.amperage,
        u.btu_rating,
        u.tonnage,
        u.breaker_size,
        u.inst_date as unit_inst_date,
        u.warranty_end_date
    FROM ServiceCalls sc
    LEFT JOIN Customers c ON sc.customer_id = c.ID
    LEFT JOIN PropertyLocations p ON sc.location_id = p.ID
    LEFT JOIN Units u ON sc.unit_id = u.unit_id
    WHERE sc.ID = ?
    """
    with get_conn() as conn:
        cursor = conn.execute(query, (call_id,))
        result = cursor.fetchone()
        return dict(result) if result else None


def list_service_calls(
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List service calls with optional filters"""
    query = """
    SELECT 
        sc.*,
        c.company as customer_name,
        p.address1 as location_address,
        u.unit_tag as unit_name,
        u.equipment_type,
        u.refrigerant_type,
        u.voltage,
        u.amperage,
        u.btu_rating,
        u.tonnage,
        u.breaker_size,
        u.inst_date as unit_inst_date,
        u.warranty_end_date
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


def update_service_call(call_id: int, data: Dict[str, Any]) -> bool:
    """Update existing service call"""
    fields = []
    params = []
    
    allowed_fields = [
        "title", "description", "priority", "status",
        "location_id", "unit_id", "closed",
        "materials_services", "labor_description"
    ]
    
    for field in allowed_fields:
        if field in data:
            fields.append(f"{field} = ?")
            params.append(data[field])
    
    if not fields:
        return False
    
    # Auto-set closed date when status becomes Closed
    if data.get("status") == "Closed" and "closed" not in data:
        fields.append("closed = datetime('now')")
    
    query = f"UPDATE ServiceCalls SET {', '.join(fields)} WHERE ID = ?"
    params.append(call_id)
    
    with get_conn() as conn:
        cursor = conn.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0


def delete_service_call(call_id: int) -> bool:
    """Delete service call"""
    query = "DELETE FROM ServiceCalls WHERE ID = ?"
    with get_conn() as conn:
        cursor = conn.execute(query, (call_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_service_call_stats(customer_id: Optional[int] = None) -> Dict[str, Any]:
    """Get service call statistics"""
    where_clause = "WHERE customer_id = ?" if customer_id else ""
    params = (customer_id,) if customer_id else ()
    
    query = f"""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
        SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
        SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as closed,
        SUM(CASE WHEN priority = 'Emergency' THEN 1 ELSE 0 END) as emergency,
        SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high,
        SUM(CASE WHEN priority = 'Normal' THEN 1 ELSE 0 END) as normal,
        SUM(CASE WHEN priority = 'Low' THEN 1 ELSE 0 END) as low
    FROM ServiceCalls {where_clause}
    """
    
    with get_conn() as conn:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else {}


def search_service_calls(search_term: str, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Search service calls by ID, title, or description"""
    query = """
    SELECT 
        sc.*,
        c.company as customer_name,
        p.address1 as location_address,
        u.unit_tag as unit_name
    FROM ServiceCalls sc
    LEFT JOIN Customers c ON sc.customer_id = c.ID
    LEFT JOIN PropertyLocations p ON sc.location_id = p.ID
    LEFT JOIN Units u ON sc.unit_id = u.unit_id
    WHERE (
        CAST(sc.ID AS TEXT) LIKE ? OR
        sc.title LIKE ? OR
        sc.description LIKE ?
    )
    """
    params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
    
    if customer_id:
        query += " AND sc.customer_id = ?"
        params.append(customer_id)
    
    query += " ORDER BY sc.created DESC LIMIT 50"
    
    with get_conn() as conn:
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_recent_calls_for_unit(unit_id: int, customer_id: int, hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent service calls for a specific unit (for duplicate prevention)"""
    query = """
    SELECT ID, created, status, title
    FROM ServiceCalls
    WHERE customer_id = ?
        AND unit_id = ?
        AND created >= datetime('now', ?)
    ORDER BY created DESC
    """

    with get_conn() as conn:
        cursor = conn.execute(query, (customer_id, unit_id, f"-{hours} hours"))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
