# core/settings_repo.py
# Repository for managing all system settings and configuration

from typing import Any, Dict, List, Optional
from core.db import get_conn
import json

def _dicts(rows):
    """Convert sqlite3.Row objects to dictionaries"""
    return [dict(r) for r in rows]


# ============================================
# COMPANY PROFILE
# ============================================

def get_company_profile() -> Dict[str, Any]:
    """Get company profile settings"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM CompanyInfo WHERE id=1").fetchone()
        return dict(row) if row else {}


def update_company_profile(data: Dict[str, Any]) -> bool:
    """Update company profile"""
    with get_conn() as conn:
        try:
            # Helper to safely get and strip values
            def safe_strip(key):
                val = data.get(key, "")
                return (val or "").strip()
            
            conn.execute("INSERT OR IGNORE INTO CompanyInfo (id, name) VALUES (1, '')")
            conn.execute("""
                UPDATE CompanyInfo
                SET name=?, address1=?, address2=?, city=?, state=?, zip=?,
                    phone=?, fax=?, email=?, website=?, service_email=?, owner_email=?,
                    logo_path=?
                WHERE id=1
            """, (
                safe_strip("name"),
                safe_strip("address1"),
                safe_strip("address2"),
                safe_strip("city"),
                safe_strip("state"),
                safe_strip("zip"),
                safe_strip("phone"),
                safe_strip("fax"),
                safe_strip("email"),
                safe_strip("website"),
                safe_strip("service_email"),
                safe_strip("owner_email"),
                safe_strip("logo_path"),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating company profile: {e}")
            return False


# ============================================
# EMAIL SETTINGS
# ============================================

def get_email_settings() -> Dict[str, Any]:
    """Get email/SMTP settings"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM EmailSettings WHERE id=1").fetchone()
        return dict(row) if row else {}


def update_email_settings(data: Dict[str, Any]) -> bool:
    """Update email/SMTP settings"""
    with get_conn() as conn:
        try:
            conn.execute("""
                UPDATE EmailSettings
                SET smtp_host=?, smtp_port=?, use_tls=?, smtp_user=?, smtp_pass=?, smtp_from=?
                WHERE id=1
            """, (
                data.get("smtp_host", "").strip(),
                int(data.get("smtp_port") or 587),
                1 if data.get("use_tls") else 0,
                data.get("smtp_user", "").strip(),
                data.get("smtp_pass", "").strip(),
                data.get("smtp_from", "").strip(),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating email settings: {e}")
            return False


# ============================================
# EMPLOYEE PROFILE
# ============================================

def list_employees(search: str = "", status: str = "") -> List[Dict[str, Any]]:
    """List all employees with optional filtering"""
    search = (search or "").strip()
    status = (status or "").strip()
    
    like = f"%{search}%"
    sql = "SELECT * FROM EmployeeProfile WHERE 1=1"
    params = []
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if search:
        sql += " AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR employee_id LIKE ?)"
        params.extend([like] * 4)
    
    sql += " ORDER BY first_name, last_name"
    
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return _dicts(rows)


def get_employee(employee_id: int) -> Dict[str, Any]:
    """Get single employee by ID"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM EmployeeProfile WHERE id=?", (employee_id,)).fetchone()
        return dict(row) if row else {}


def create_employee(data: Dict[str, Any]) -> Optional[int]:
    """Create new employee"""
    with get_conn() as conn:
        try:
            cur = conn.execute("""
                INSERT INTO EmployeeProfile 
                (employee_id, first_name, last_name, photo_path, department, position, 
                 email, phone, mobile, address1, address2, city, state, zip, start_date, 
                 status, emergency_contact, emergency_phone, notes, can_login, mfa_enabled,
                 security_clearance, access_scope, password_last_reset)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("employee_id", "").strip(),
                data.get("first_name", "").strip(),
                data.get("last_name", "").strip(),
                data.get("photo_path", ""),
                data.get("department", "").strip(),
                data.get("position", "").strip(),
                data.get("email", "").strip(),
                data.get("phone", "").strip(),
                data.get("mobile", "").strip(),
                data.get("address1", "").strip(),
                data.get("address2", "").strip(),
                data.get("city", "").strip(),
                data.get("state", "").strip(),
                data.get("zip", "").strip(),
                data.get("start_date", ""),
                data.get("status", "Active"),
                data.get("emergency_contact", "").strip(),
                data.get("emergency_phone", "").strip(),
                data.get("notes", "").strip(),
                1 if data.get("can_login") else 0,
                1 if data.get("mfa_enabled") else 0,
                data.get("security_clearance", "").strip(),
                data.get("access_scope", "").strip(),
                data.get("password_last_reset", "").strip(),
            ))
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"Error creating employee: {e}")
            return None


def update_employee(employee_id: int, data: Dict[str, Any]) -> bool:
    """Update employee information"""
    with get_conn() as conn:
        try:
            conn.execute("""
                UPDATE EmployeeProfile
                SET first_name=?, last_name=?, photo_path=?, department=?, position=?,
                    email=?, phone=?, mobile=?, address1=?, address2=?, city=?, state=?, zip=?,
                    start_date=?, status=?, emergency_contact=?, emergency_phone=?, notes=?,
                    can_login=?, mfa_enabled=?, security_clearance=?, access_scope=?,
                    password_last_reset=?, updated=datetime('now')
                WHERE id=?
            """, (
                data.get("first_name", "").strip(),
                data.get("last_name", "").strip(),
                data.get("photo_path", ""),
                data.get("department", "").strip(),
                data.get("position", "").strip(),
                data.get("email", "").strip(),
                data.get("phone", "").strip(),
                data.get("mobile", "").strip(),
                data.get("address1", "").strip(),
                data.get("address2", "").strip(),
                data.get("city", "").strip(),
                data.get("state", "").strip(),
                data.get("zip", "").strip(),
                data.get("start_date", ""),
                data.get("status", "Active"),
                data.get("emergency_contact", "").strip(),
                data.get("emergency_phone", "").strip(),
                data.get("notes", "").strip(),
                1 if data.get("can_login") else 0,
                1 if data.get("mfa_enabled") else 0,
                data.get("security_clearance", "").strip(),
                data.get("access_scope", "").strip(),
                data.get("password_last_reset", "").strip(),
                employee_id,
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating employee: {e}")
            return False


def delete_employee(employee_id: int) -> bool:
    """Delete employee"""
    with get_conn() as conn:
        try:
            conn.execute("DELETE FROM EmployeeProfile WHERE id=?", (employee_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting employee: {e}")
            return False


# ============================================
# SERVICE CALL SETTINGS
# ============================================

def get_service_call_settings() -> Dict[str, Any]:
    """Get service call configuration"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM ServiceCallSettings WHERE id=1").fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields if present
            if result.get("priority_colors"):
                try:
                    result["priority_colors"] = json.loads(result["priority_colors"])
                except:
                    result["priority_colors"] = {}
            if result.get("status_workflow"):
                try:
                    result["status_workflow"] = json.loads(result["status_workflow"])
                except:
                    result["status_workflow"] = []
            return result
        return {}


def update_service_call_settings(data: Dict[str, Any]) -> bool:
    """Update service call settings"""
    with get_conn() as conn:
        try:
            # Ensure the row exists
            conn.execute("""
                INSERT OR IGNORE INTO ServiceCallSettings (id)
                VALUES (1)
            """)
            
            priority_colors = json.dumps(data.get("priority_colors", {})) if data.get("priority_colors") else None
            status_workflow = json.dumps(data.get("status_workflow", [])) if data.get("status_workflow") else None
            
            conn.execute("""
                UPDATE ServiceCallSettings
                SET default_priority=?, auto_assign=?, assignment_method=?, 
                    priority_colors=?, status_workflow=?, notification_on_create=?,
                    notification_on_close=?, sla_hours_low=?, sla_hours_normal=?,
                    sla_hours_high=?, sla_hours_emergency=?
                WHERE id=1
            """, (
                data.get("default_priority", "Normal"),
                1 if data.get("auto_assign") else 0,
                data.get("assignment_method", "manual"),
                priority_colors,
                status_workflow,
                1 if data.get("notification_on_create") else 0,
                1 if data.get("notification_on_close") else 0,
                int(data.get("sla_hours_low") or 72),
                int(data.get("sla_hours_normal") or 48),
                int(data.get("sla_hours_high") or 24),
                int(data.get("sla_hours_emergency") or 4),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating service call settings: {e}")
            return False


# ============================================
# TICKET SEQUENCE
# ============================================

def list_ticket_sequences() -> List[Dict[str, Any]]:
    """List all ticket sequence types"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM TicketSequenceSettings ORDER BY sequence_type"
        ).fetchall()
        return _dicts(rows)


def get_ticket_sequence(sequence_id: int) -> Dict[str, Any]:
    """Get specific ticket sequence"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM TicketSequenceSettings WHERE id=?", (sequence_id,)
        ).fetchone()
        return dict(row) if row else {}


def create_ticket_sequence(data: Dict[str, Any]) -> Optional[int]:
    """Create new ticket sequence"""
    with get_conn() as conn:
        try:
            cur = conn.execute("""
                INSERT INTO TicketSequenceSettings
                (sequence_type, prefix, starting_number, current_number, 
                 increment_by, format_pattern, reset_period, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("sequence_type", "").strip(),
                data.get("prefix", "").strip(),
                int(data.get("starting_number") or 1000),
                int(data.get("current_number") or 1000),
                int(data.get("increment_by") or 1),
                data.get("format_pattern", "{prefix}-{seq:05d}"),
                data.get("reset_period", "none"),
                1 if data.get("is_active") else 0,
            ))
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"Error creating ticket sequence: {e}")
            return None


def update_ticket_sequence(sequence_id: int, data: Dict[str, Any]) -> bool:
    """Update ticket sequence"""
    with get_conn() as conn:
        try:
            conn.execute("""
                UPDATE TicketSequenceSettings
                SET sequence_type=?, prefix=?, starting_number=?, current_number=?,
                    increment_by=?, format_pattern=?, reset_period=?, is_active=?,
                    updated=datetime('now')
                WHERE id=?
            """, (
                data.get("sequence_type", "").strip(),
                data.get("prefix", "").strip(),
                int(data.get("starting_number") or 1000),
                int(data.get("current_number") or 1000),
                int(data.get("increment_by") or 1),
                data.get("format_pattern", "{prefix}-{seq:05d}"),
                data.get("reset_period", "none"),
                1 if data.get("is_active") else 0,
                sequence_id,
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating ticket sequence: {e}")
            return False


def delete_ticket_sequence(sequence_id: int) -> bool:
    """Delete ticket sequence"""
    with get_conn() as conn:
        try:
            conn.execute("DELETE FROM TicketSequenceSettings WHERE id=?", (sequence_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting ticket sequence: {e}")
            return False


def get_next_ticket_number(sequence_type: str) -> str:
    """Generate next ticket number for given sequence type"""
    with get_conn() as conn:
        try:
            row = conn.execute(
                "SELECT * FROM TicketSequenceSettings WHERE sequence_type=?",
                (sequence_type,)
            ).fetchone()
            
            if not row:
                return ""
            
            result = dict(row)
            current = result.get("current_number", 1000)
            increment = result.get("increment_by", 1)
            prefix = result.get("prefix", "")
            
            # Update to next number
            next_number = current + increment
            conn.execute(
                "UPDATE TicketSequenceSettings SET current_number=? WHERE id=?",
                (next_number, result.get("id"))
            )
            conn.commit()
            
            # Format according to pattern (simple formatting for now)
            if prefix:
                return f"{prefix}-{current:05d}"
            return str(current)
        except Exception as e:
            print(f"Error getting next ticket number: {e}")
            return ""
