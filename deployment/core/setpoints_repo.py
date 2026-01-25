"""
Repository for Unit Setpoint Control & Schedule Management
"""
from typing import Optional, Dict, Any, List
from .db import get_conn


def get_unit_setpoint(unit_id: int) -> Optional[Dict[str, Any]]:
    """Get current setpoint config for a unit"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM UnitSetpoints WHERE unit_id = ?",
            (unit_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_or_update_setpoint(
    unit_id: int,
    mode: str,
    cooling_setpoint: float,
    heating_setpoint: float,
    deadband: float,
    fan: str = "Auto",
    thermostat_name: str = "",
    schedule_enabled: int = 0,
    schedule_day: str = "Daily",
    schedule_start_time: str = "09:00",
    schedule_end_time: str = "17:00",
    schedule_mode: str = "Cooling",
    schedule_temp: float = 72.0,
    updated_by_login_id: Optional[int] = None
) -> bool:
    """Create or update setpoint for a unit"""
    conn = get_conn()
    try:
        # Check if exists
        existing = conn.execute(
            "SELECT id FROM UnitSetpoints WHERE unit_id = ?",
            (unit_id,)
        ).fetchone()
        
        if existing:
            # Update
            conn.execute(
                """
                UPDATE UnitSetpoints
                SET mode = ?, cooling_setpoint = ?, heating_setpoint = ?, deadband = ?, fan = ?, thermostat_name = ?,
                    schedule_enabled = ?, schedule_day = ?, schedule_start_time = ?,
                    schedule_end_time = ?, schedule_mode = ?, schedule_temp = ?,
                    updated = datetime('now'), updated_by_login_id = ?
                WHERE unit_id = ?
                """,
                (
                    mode, cooling_setpoint, heating_setpoint, deadband, fan, thermostat_name,
                    schedule_enabled, schedule_day, schedule_start_time,
                    schedule_end_time, schedule_mode, schedule_temp,
                    updated_by_login_id, unit_id
                )
            )
        else:
            # Insert
            conn.execute(
                """
                INSERT INTO UnitSetpoints
                (unit_id, mode, cooling_setpoint, heating_setpoint, deadband, fan, thermostat_name,
                 schedule_enabled, schedule_day, schedule_start_time,
                 schedule_end_time, schedule_mode, schedule_temp, updated_by_login_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    unit_id, mode, cooling_setpoint, heating_setpoint, deadband, fan, thermostat_name,
                    schedule_enabled, schedule_day, schedule_start_time,
                    schedule_end_time, schedule_mode, schedule_temp,
                    updated_by_login_id
                )
            )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating setpoint: {e}")
        return False
    finally:
        conn.close()


def get_all_setpoints() -> List[Dict[str, Any]]:
    """Get all unit setpoints"""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM UnitSetpoints").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_setpoint(unit_id: int) -> bool:
    """Delete setpoint for a unit"""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM UnitSetpoints WHERE unit_id = ?", (unit_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()
