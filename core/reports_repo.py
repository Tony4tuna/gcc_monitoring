"""
Reports Repository - All Report Queries for GCC Monitoring System
Generates various analytical reports based on system data
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from core.db import get_conn


# ============================================
# HIERARCHICAL COMPANY REPORTS
# ============================================

def get_company_profile() -> Dict[str, Any]:
    """
    Get company profile information
    """
    from core.db import get_conn
    
    default_profile = {
        "company": "GCC TECHNOLOGY",
        "address1": "123 Tech Street",
        "address2": "",
        "city": "Tech City",
        "state": "TC",
        "zip": "12345",
        "phone": "(555) 123-4567",
        "email": "support@gcc.com",
        "service_email": "service@gcc.com",
        "website": "www.gcc.com"
    }
    
    try:
        conn = get_conn()
        # Try CompanyProfile first
        row = conn.execute("SELECT * FROM CompanyProfile LIMIT 1").fetchone()
        if not row:
            # Fallback to CompanyInfo
            row = conn.execute("SELECT * FROM CompanyInfo LIMIT 1").fetchone()
        
        if row:
            row_dict = dict(row)
            return {
                "company": row_dict.get("company_name") or row_dict.get("name") or row_dict.get("company") or default_profile["company"],
                "address1": row_dict.get("address1") or "",
                "address2": row_dict.get("address2") or "",
                "city": row_dict.get("city") or "",
                "state": row_dict.get("state") or "",
                "zip": row_dict.get("zip") or "",
                "phone": row_dict.get("phone") or row_dict.get("fax") or default_profile["phone"],
                "email": row_dict.get("email") or default_profile["email"],
                "service_email": row_dict.get("service_email") or row_dict.get("email") or "",
                "website": row_dict.get("website") or default_profile["website"],
            }
        conn.close()
    except Exception:
        pass
    
    return default_profile


def get_hierarchical_company_report(customer_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Hierarchical Company Report
    Structure: Company → Customers → Locations → Equipment
    Returns nested dictionary with full hierarchy
    """
    conn = get_conn()
    try:
        # Company Profile
        company_profile = get_company_profile()
        
        # Customers
        customer_filter = ""
        params = []
        if customer_id:
            customer_filter = "WHERE c.ID = ?"
            params.append(customer_id)
        
        customers_data = conn.execute(f"""
            SELECT 
                c.ID as customer_id,
                c.company,
                c.first_name,
                c.last_name,
                c.email,
                c.phone1,
                c.mobile,
                c.address1,
                c.city,
                c.state,
                c.zip,
                c.website,
                c.created,
                COUNT(DISTINCT pl.ID) as location_count,
                COUNT(DISTINCT u.unit_id) as equipment_count
            FROM Customers c
            LEFT JOIN PropertyLocations pl ON c.ID = pl.customer_id
            LEFT JOIN Units u ON pl.ID = u.location_id
            {customer_filter}
            GROUP BY c.ID
            ORDER BY c.company
        """, params).fetchall()
        
        customers = []
        for cust_row in customers_data:
            cust = dict(cust_row)
            cust_id = cust["customer_id"]
            
            # Get locations for this customer
            locations_data = conn.execute("""
                SELECT 
                    pl.ID as location_id,
                    pl.address1,
                    pl.address2,
                    pl.city,
                    pl.state,
                    pl.zip,
                    pl.contact,
                    pl.job_phone,
                    COUNT(DISTINCT u.unit_id) as equipment_count
                FROM PropertyLocations pl
                LEFT JOIN Units u ON pl.ID = u.location_id
                WHERE pl.customer_id = ?
                GROUP BY pl.ID
                ORDER BY pl.address1
            """, (cust_id,)).fetchall()
            
            locations = []
            for loc_row in locations_data:
                loc = dict(loc_row)
                loc_id = loc["location_id"]
                
                # Get equipment for this location
                equipment_data = conn.execute("""
                    SELECT 
                        u.unit_id,
                        u.unit_tag,
                        u.make,
                        u.model,
                        u.serial,
                        u.inst_date
                    FROM Units u
                    WHERE u.location_id = ?
                    ORDER BY u.unit_tag
                """, (loc_id,)).fetchall()
                
                loc["equipment"] = [dict(eq) for eq in equipment_data]
                locations.append(loc)
            
            cust["locations"] = locations
            customers.append(cust)
        
        return {
            "company_profile": company_profile,
            "customers": customers,
            "total_customers": len(customers),
            "total_locations": sum(len(c["locations"]) for c in customers),
            "total_equipment": sum(len(loc["equipment"]) for c in customers for loc in c["locations"])
        }
    finally:
        conn.close()


# ============================================
# EQUIPMENT REPORTS
# ============================================

def get_equipment_inventory_report(customer_id: Optional[int] = None, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Equipment Inventory Report
    Lists all equipment with full specifications, organized by customer/location
    """
    conn = get_conn()
    try:
        filters = []
        params = []
        
        if customer_id:
            filters.append("c.ID = ?")
            params.append(customer_id)
        
        if location_id:
            filters.append("pl.ID = ?")
            params.append(location_id)
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        rows = conn.execute(f"""
            SELECT 
                c.ID as customer_id,
                c.company as customer_name,
                pl.ID as location_id,
                pl.address1 as location_address,
                pl.city as location_city,
                pl.state as location_state,
                u.unit_id,
                u.unit_tag,
                u.make,
                u.model,
                u.serial,
                u.inst_date
            FROM Units u
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            {where_clause}
            ORDER BY c.company, pl.address1, u.unit_tag
        """, params).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_equipment_by_age_report() -> List[Dict[str, Any]]:
    """
    Equipment Age Report
    Groups equipment by installation date and warranty status
    """
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT 
                u.unit_id,
                u.unit_tag,
                u.make,
                u.model,
                u.inst_date,
                c.company as customer_name,
                pl.address1 as location_address,
                CASE
                    WHEN u.inst_date IS NULL THEN 'Unknown'
                    WHEN CAST((JULIANDAY('now') - JULIANDAY(u.inst_date)) / 365.25 AS INTEGER) < 5 THEN '0-5 years'
                    WHEN CAST((JULIANDAY('now') - JULIANDAY(u.inst_date)) / 365.25 AS INTEGER) < 10 THEN '5-10 years'
                    WHEN CAST((JULIANDAY('now') - JULIANDAY(u.inst_date)) / 365.25 AS INTEGER) < 15 THEN '10-15 years'
                    ELSE '15+ years'
                END as age_group
            FROM Units u
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            ORDER BY u.inst_date DESC
        """).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_equipment_maintenance_history(unit_id: Optional[int] = None, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Equipment Maintenance History Report
    Shows all service tickets per unit with timeline
    """
    conn = get_conn()
    try:
        filters = []
        params = []
        
        if unit_id:
            filters.append("u.unit_id = ?")
            params.append(unit_id)
        
        if customer_id:
            filters.append("c.ID = ?")
            params.append(customer_id)
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        rows = conn.execute(f"""
            SELECT 
                sc.ID as ticket_id,
                sc.created as service_date,
                sc.closed as completion_date,
                sc.status,
                sc.priority,
                sc.title,
                sc.materials_services,
                sc.labor_description,
                u.unit_id,
                u.unit_tag,
                u.make,
                u.model,
                c.company as customer_name,
                pl.address1 as location_address,
                l.login_id as technician
            FROM ServiceCalls sc
            JOIN Units u ON sc.unit_id = u.unit_id
            JOIN PropertyLocations pl ON sc.location_id = pl.ID
            JOIN Customers c ON sc.customer_id = c.ID
            LEFT JOIN Logins l ON sc.requested_by_login_id = l.ID
            {where_clause}
            ORDER BY sc.created DESC
        """, params).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ============================================
# SERVICE TICKET REPORTS
# ============================================

def get_tickets_by_status_report(status: Optional[str] = None, customer_id: Optional[int] = None, 
                                  start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Service Tickets Report
    Filter by status, customer, date range
    """
    conn = get_conn()
    try:
        filters = []
        params = []
        
        if status:
            filters.append("sc.status = ?")
            params.append(status)
        
        if customer_id:
            filters.append("sc.customer_id = ?")
            params.append(customer_id)
        
        if start_date:
            filters.append("DATE(sc.created) >= DATE(?)")
            params.append(start_date)
        
        if end_date:
            filters.append("DATE(sc.created) <= DATE(?)")
            params.append(end_date)
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        rows = conn.execute(f"""
            SELECT 
                sc.ID as ticket_id,
                sc.created,
                sc.closed,
                sc.status,
                sc.priority,
                sc.title,
                sc.description,
                sc.materials_services,
                sc.labor_description,
                c.company as customer_name,
                c.phone1 as customer_phone,
                pl.address1 as location_address,
                pl.city as location_city,
                pl.state as location_state,
                u.unit_tag,
                u.make,
                u.model,
                l.login_id as requested_by,
                CASE 
                    WHEN sc.closed IS NULL THEN NULL
                    ELSE CAST((JULIANDAY(sc.closed) - JULIANDAY(sc.created)) * 24 AS REAL)
                END as resolution_hours
            FROM ServiceCalls sc
            JOIN Customers c ON sc.customer_id = c.ID
            LEFT JOIN PropertyLocations pl ON sc.location_id = pl.ID
            LEFT JOIN Units u ON sc.unit_id = u.unit_id
            LEFT JOIN Logins l ON sc.requested_by_login_id = l.ID
            {where_clause}
            ORDER BY sc.created DESC
        """, params).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_ticket_resolution_analysis(days: int = 30) -> Dict[str, Any]:
    """
    Ticket Resolution Time Analysis
    Average resolution time by priority and customer
    """
    conn = get_conn()
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Overall stats
        overall = conn.execute("""
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(CASE WHEN closed IS NOT NULL THEN 1 END) as closed_tickets,
                AVG(CASE 
                    WHEN closed IS NOT NULL 
                    THEN (JULIANDAY(closed) - JULIANDAY(created)) * 24 
                END) as avg_resolution_hours
            FROM ServiceCalls
            WHERE DATE(created) >= DATE(?)
        """, (cutoff_date,)).fetchone()
        
        # By priority
        by_priority = conn.execute("""
            SELECT 
                priority,
                COUNT(*) as count,
                AVG(CASE 
                    WHEN closed IS NOT NULL 
                    THEN (JULIANDAY(closed) - JULIANDAY(created)) * 24 
                END) as avg_resolution_hours
            FROM ServiceCalls
            WHERE DATE(created) >= DATE(?)
            GROUP BY priority
            ORDER BY 
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Normal' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END
        """, (cutoff_date,)).fetchall()
        
        # By customer (top 10)
        by_customer = conn.execute("""
            SELECT 
                c.company as customer_name,
                COUNT(*) as ticket_count,
                AVG(CASE 
                    WHEN sc.closed IS NOT NULL 
                    THEN (JULIANDAY(sc.closed) - JULIANDAY(sc.created)) * 24 
                END) as avg_resolution_hours
            FROM ServiceCalls sc
            JOIN Customers c ON sc.customer_id = c.ID
            WHERE DATE(sc.created) >= DATE(?)
            GROUP BY sc.customer_id, c.company
            ORDER BY ticket_count DESC
            LIMIT 10
        """, (cutoff_date,)).fetchall()
        
        return {
            "period_days": days,
            "overall": dict(overall) if overall else {},
            "by_priority": [dict(r) for r in by_priority],
            "by_customer": [dict(r) for r in by_customer]
        }
    finally:
        conn.close()


def get_open_tickets_summary() -> List[Dict[str, Any]]:
    """
    Open Tickets Summary
    All currently open tickets grouped by priority
    """
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT 
                sc.ID as ticket_id,
                sc.created,
                sc.priority,
                sc.title,
                c.company as customer_name,
                pl.address1 as location_address,
                u.unit_tag,
                CAST((JULIANDAY('now') - JULIANDAY(sc.created)) AS INTEGER) as days_open
            FROM ServiceCalls sc
            JOIN Customers c ON sc.customer_id = c.ID
            LEFT JOIN PropertyLocations pl ON sc.location_id = pl.ID
            LEFT JOIN Units u ON sc.unit_id = u.unit_id
            WHERE sc.status IN ('Open', 'Pending', 'In Progress')
            ORDER BY 
                CASE sc.priority
                    WHEN 'High' THEN 1
                    WHEN 'Normal' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END,
                sc.created ASC
        """).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ============================================
# CUSTOMER REPORTS
# ============================================

def get_customer_summary_report(customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Customer Summary Report
    Overview of all customers with location/equipment counts and activity
    """
    conn = get_conn()
    try:
        filters = []
        params = []
        
        if customer_id:
            filters.append("c.ID = ?")
            params.append(customer_id)
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        rows = conn.execute(f"""
            SELECT 
                c.ID as customer_id,
                c.company as customer_name,
                c.email as customer_email,
                c.phone1 as customer_phone,
                c.address1,
                c.city,
                c.state,
                c.zip,
                COUNT(DISTINCT pl.ID) as location_count,
                COUNT(DISTINCT u.unit_id) as equipment_count,
                COUNT(DISTINCT CASE WHEN sc.status IN ('Open', 'Pending', 'In Progress') THEN sc.ID END) as open_tickets,
                COUNT(DISTINCT sc.ID) as total_tickets,
                MAX(sc.created) as last_service_date
            FROM Customers c
            LEFT JOIN PropertyLocations pl ON c.ID = pl.customer_id
            LEFT JOIN Units u ON pl.ID = u.location_id
            LEFT JOIN ServiceCalls sc ON c.ID = sc.customer_id
            {where_clause}
            GROUP BY c.ID
            ORDER BY c.company
        """, params).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_customer_activity_report(customer_id: int, days: int = 90) -> Dict[str, Any]:
    """
    Customer Activity Detail Report
    Comprehensive activity for a specific customer
    """
    conn = get_conn()
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Customer info
        customer = conn.execute("""
            SELECT * FROM Customers WHERE ID = ?
        """, (customer_id,)).fetchone()
        
        # Locations
        locations = conn.execute("""
            SELECT 
                pl.*,
                COUNT(DISTINCT u.unit_id) as equipment_count
            FROM PropertyLocations pl
            LEFT JOIN Units u ON pl.ID = u.location_id
            WHERE pl.customer_id = ?
            GROUP BY pl.ID
        """, (customer_id,)).fetchall()
        
        # Recent tickets
        tickets = conn.execute("""
            SELECT 
                sc.*,
                pl.address1 as location_address,
                u.unit_tag
            FROM ServiceCalls sc
            LEFT JOIN PropertyLocations pl ON sc.location_id = pl.ID
            LEFT JOIN Units u ON sc.unit_id = u.unit_id
            WHERE sc.customer_id = ?
                AND DATE(sc.created) >= DATE(?)
            ORDER BY sc.created DESC
        """, (customer_id, cutoff_date)).fetchall()
        
        return {
            "customer": dict(customer) if customer else {},
            "locations": [dict(r) for r in locations],
            "recent_tickets": [dict(r) for r in tickets]
        }
    finally:
        conn.close()


# ============================================
# LOCATION REPORTS
# ============================================

def get_location_inventory_report(location_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Location Inventory Report
    All locations with equipment counts and status
    """
    conn = get_conn()
    try:
        filters = []
        params = []
        
        if location_id:
            filters.append("pl.ID = ?")
            params.append(location_id)
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        rows = conn.execute(f"""
            SELECT 
                pl.ID as location_id,
                pl.address1,
                pl.address2,
                pl.city,
                pl.state,
                pl.zip,
                pl.contact,
                pl.job_phone,
                c.company as customer_name,
                c.phone1 as customer_phone,
                COUNT(DISTINCT u.unit_id) as equipment_count
            FROM PropertyLocations pl
            JOIN Customers c ON pl.customer_id = c.ID
            LEFT JOIN Units u ON pl.ID = u.location_id
            {where_clause}
            GROUP BY pl.ID
            ORDER BY c.company, pl.address1
        """, params).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ============================================
# ALERT & TELEMETRY REPORTS
# ============================================

def get_alert_history_report(days: int = 30, unit_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Alert History Report
    Historical alerts from unit readings
    """
    conn = get_conn()
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        filters = ["DATE(ur.ts) >= DATE(?)"]
        params = [cutoff_date]
        
        if unit_id:
            filters.append("ur.unit_id = ?")
            params.append(unit_id)
        
        where_clause = f"WHERE {' AND '.join(filters)}"
        
        rows = conn.execute(f"""
            SELECT 
                ur.reading_id,
                ur.unit_id,
                ur.ts as timestamp,
                ur.mode,
                ur.fault_code,
                ur.alarm_status,
                ur.alert_message,
                ur.supply_temp,
                ur.return_temp,
                u.unit_tag,
                u.make,
                u.model,
                pl.address1 as location_address,
                c.company as customer_name
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            {where_clause}
                AND (ur.fault_code IS NOT NULL 
                     OR ur.alarm_status = 'Active'
                     OR ur.mode = 'Fault')
            ORDER BY ur.ts DESC
        """, params).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_current_alerts_report() -> List[Dict[str, Any]]:
    """
    Current Alerts Report
    Latest reading for units with active alerts
    """
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT 
                u.unit_id,
                u.unit_tag,
                u.make,
                u.model,
                u.equipment_type,
                u.status,
                pl.address1 as location_address,
                c.company as customer_name,
                ur.ts as last_reading,
                ur.mode,
                ur.fault_code,
                ur.supply_temp,
                ur.return_temp,
                ur.alarm_status,
                ur.alert_message
            FROM Units u
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            LEFT JOIN UnitReadings ur ON u.unit_id = ur.unit_id
            WHERE ur.reading_id IN (
                SELECT MAX(reading_id) FROM UnitReadings GROUP BY unit_id
            )
            AND (u.status IN ('warning', 'error')
                 OR ur.fault_code IS NOT NULL
                 OR ur.alarm_status = 'Active'
                 OR ur.mode = 'Fault')
            ORDER BY 
                CASE u.status
                    WHEN 'error' THEN 1
                    WHEN 'warning' THEN 2
                    ELSE 3
                END,
                c.company, pl.address1
        """).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_temperature_trend_report(unit_id: int, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Temperature Trend Report
    Temperature readings over time for specific unit
    """
    conn = get_conn()
    try:
        cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        rows = conn.execute("""
            SELECT 
                ur.reading_id,
                ur.ts as timestamp,
                ur.supply_temp,
                ur.return_temp,
                ur.i_temp as indoor_temp,
                ur.o_temp as outdoor_temp,
                ur.delta_t,
                ur.sp_1 as cooling_setpoint,
                ur.sp_2 as heating_setpoint,
                ur.mode,
                u.unit_tag,
                u.make,
                u.model
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            WHERE ur.unit_id = ?
                AND ur.ts >= ?
            ORDER BY ur.ts ASC
        """, (unit_id, cutoff_time)).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ============================================
# SUMMARY/DASHBOARD REPORTS
# ============================================

def get_system_overview_report() -> Dict[str, Any]:
    """
    System Overview Report
    High-level stats for entire system
    """
    conn = get_conn()
    try:
        # Customer stats
        customer_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_customers,
                COUNT(CASE WHEN created >= DATE('now', '-30 days') THEN 1 END) as new_customers_30d
            FROM Customers
        """).fetchone()
        
        # Location stats
        location_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_locations,
                COUNT(DISTINCT customer_id) as customers_with_locations
            FROM PropertyLocations
        """).fetchone()
        
        # Equipment stats
        equipment_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_units
            FROM Units
        """).fetchone()
        
        # Ticket stats
        ticket_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(CASE WHEN status IN ('Open', 'Pending', 'In Progress') THEN 1 END) as open_tickets,
                COUNT(CASE WHEN status = 'Closed' THEN 1 END) as closed_tickets,
                COUNT(CASE WHEN DATE(created) >= DATE('now', '-7 days') THEN 1 END) as tickets_7d,
                COUNT(CASE WHEN DATE(created) >= DATE('now', '-30 days') THEN 1 END) as tickets_30d
            FROM ServiceCalls
        """).fetchone()
        
        # Recent activity
        recent_activity = conn.execute("""
            SELECT 
                'ticket' as activity_type,
                sc.ID as id,
                sc.title as description,
                sc.created as timestamp,
                c.company as customer_name
            FROM ServiceCalls sc
            JOIN Customers c ON sc.customer_id = c.ID
            ORDER BY sc.created DESC
            LIMIT 10
        """).fetchall()
        
        return {
            "customer_stats": dict(customer_stats) if customer_stats else {},
            "location_stats": dict(location_stats) if location_stats else {},
            "equipment_stats": dict(equipment_stats) if equipment_stats else {},
            "ticket_stats": dict(ticket_stats) if ticket_stats else {},
            "recent_activity": [dict(r) for r in recent_activity]
        }
    finally:
        conn.close()


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_available_report_types() -> List[Dict[str, str]]:
    """
    Return list of all available report types with descriptions
    """
    return [
        {
            "category": "Equipment",
            "reports": [
                {"id": "equipment_inventory", "name": "Equipment Inventory", "description": "Complete equipment list with specifications"},
                {"id": "equipment_by_age", "name": "Equipment Age Analysis", "description": "Equipment grouped by age and warranty status"},
                {"id": "equipment_maintenance", "name": "Maintenance History", "description": "Service history per equipment unit"},
            ]
        },
        {
            "category": "Service Tickets",
            "reports": [
                {"id": "tickets_by_status", "name": "Tickets by Status", "description": "Service tickets filtered by status and date"},
                {"id": "ticket_resolution", "name": "Resolution Time Analysis", "description": "Average resolution time by priority"},
                {"id": "open_tickets", "name": "Open Tickets Summary", "description": "All currently open tickets"},
            ]
        },
        {
            "category": "Customers",
            "reports": [
                {"id": "customer_summary", "name": "Customer Summary", "description": "Overview of all customers with stats"},
                {"id": "customer_activity", "name": "Customer Activity Detail", "description": "Comprehensive activity for specific customer"},
            ]
        },
        {
            "category": "Locations",
            "reports": [
                {"id": "location_inventory", "name": "Location Inventory", "description": "All locations with equipment counts"},
            ]
        },
        {
            "category": "Alerts & Monitoring",
            "reports": [
                {"id": "alert_history", "name": "Alert History", "description": "Historical alerts from telemetry data"},
                {"id": "current_alerts", "name": "Current Alerts", "description": "Units with active alerts"},
                {"id": "temperature_trend", "name": "Temperature Trend", "description": "Temperature readings over time"},
            ]
        },
        {
            "category": "System Overview",
            "reports": [
                {"id": "system_overview", "name": "System Overview", "description": "High-level system statistics"},
            ]
        }
    ]
