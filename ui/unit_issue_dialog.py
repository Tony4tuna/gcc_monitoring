# ui/unit_issue_dialog.py
from __future__ import annotations

from nicegui import ui
from core.db import get_conn
from core.auth import current_user
from core.issues_repo import list_issue_types
from core.tickets_repo import create_service_call
from core.logger import log_user_action, log_error, handle_error
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def _get_latest_reading(unit_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT *
            FROM UnitReadings
            WHERE unit_id = ?
            ORDER BY reading_id DESC
            LIMIT 1
            """,
            (unit_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _get_unit_info(unit_id: int) -> Optional[Dict[str, Any]]:
    """Get unit details with customer and location info"""
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT 
                u.unit_id, u.make, u.model, u.serial,
                pl.ID as location_id, pl.address1 as location,
                c.ID as customer_id, c.company as customer
            FROM Units u
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            WHERE u.unit_id = ?
            """,
            (unit_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _get_open_ticket_for_unit(unit_id: int) -> Optional[Dict[str, Any]]:
    """Check if unit has an open ticket"""
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM ServiceCalls
            WHERE unit_id = ? AND status IN ('Open', 'OPEN', 'In Progress', 'Pending')
            ORDER BY created DESC
            LIMIT 1
            """,
            (unit_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _check_duplicate_symptom(unit_id: int, symptom_id: int, user_id: int) -> bool:
    """Check if user created ticket with same symptom in last 24 hours"""
    conn = get_conn()
    try:
        cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM ServiceCalls
            WHERE unit_id = ? 
              AND symptom_id = ?
              AND requested_by_login_id = ?
              AND created >= ?
              AND status IN ('Open', 'OPEN', 'In Progress', 'Pending')
            """,
            (unit_id, symptom_id, user_id, cutoff),
        ).fetchone()
        return (row[0] if row else 0) > 0
    finally:
        conn.close()


def open_unit_issue_dialog(unit_id: int) -> None:
    """
    Opens dialog for faulty unit to show ticket status or create ticket.
    - Shows existing open ticket if present
    - Allows ticket creation if no open ticket
    - Clients select symptoms, Admins/Techs use technical descriptions
    """
    try:
        unit_id = int(unit_id)
        log_user_action(f"Opened unit dialog", f"Unit {unit_id}")
    except Exception as e:
        handle_error(e, "opening unit dialog")
        return

    user = current_user()
    if not user:
        ui.notify("Not logged in", type="negative")
        return

    hierarchy = int(user.get("hierarchy", 5))
    is_client = hierarchy == 4
    is_admin_or_tech = hierarchy <= 3

    try:
        unit_info = _get_unit_info(unit_id)
        if not unit_info:
            ui.notify(f"Unit {unit_id} not found", type="negative")
            return

        reading = _get_latest_reading(unit_id)
        open_ticket = _get_open_ticket_for_unit(unit_id)

        with ui.dialog().classes("w-full max-w-3xl") as dlg:
            with ui.card().classes("w-full gcc-card"):
                # Header
                ui.label(f"Unit RTU-{unit_id}").classes("text-xl font-bold")
                ui.label(f"{unit_info['customer']} • {unit_info['location']}").classes("text-sm gcc-muted")

                # Unit status
                if reading:
                    with ui.row().classes("gap-4 w-full mt-3 p-3 bg-gray-800 rounded"):
                        ui.label(f"Mode: {reading.get('mode') or '—'}").classes("text-sm")
                        ui.label(f"Temp: {reading.get('supply_temp')}°F" if reading.get('supply_temp') is not None else "Temp: —").classes("text-sm")
                        ui.label(f"Fault: {reading.get('fault_code') or 'None'}").classes("text-sm")
                        ui.label(f"Updated: {reading.get('ts') or '—'}").classes("text-xs gcc-muted")

                ui.separator().classes("my-4")

                # Check ticket status
                if open_ticket:
                    # TICKET ALREADY EXISTS
                    ui.label("⚠️ Ticket Open").classes("text-lg font-bold text-yellow-400")
                    ui.label(f"Ticket #{open_ticket.get('ticket_no') or open_ticket['ID']}").classes("text-sm")
                    ui.label(f"Status: {open_ticket['status']}").classes("text-sm")
                    ui.label(f"Created: {open_ticket['created']}").classes("text-xs gcc-muted")
                    if open_ticket.get('title'):
                        ui.label(f"Issue: {open_ticket['title']}").classes("text-sm mt-2")
                    if open_ticket.get('description'):
                        ui.label(open_ticket['description']).classes("text-xs gcc-muted mt-1")
                    
                    ui.label("A technician will address this issue.").classes("text-sm mt-3 text-green-400")
                else:
                    # NO TICKET - ALLOW CREATION
                    ui.label("🔧 No Ticket Open").classes("text-lg font-bold text-red-400")
                    ui.label("Create a service ticket for this unit").classes("text-sm gcc-muted mb-3")

                    if is_client:
                        # CLIENT: Select symptom
                        ui.label("What is the issue?").classes("text-sm font-semibold mt-2")
                        symptoms = list_issue_types(enabled_only=True)
                        
                        symptom_select = ui.select(
                            label="Select the symptom",
                            options={s['id']: s['title'] for s in symptoms},
                            with_input=True
                        ).classes("w-full mb-3")
                        
                        notes_input = ui.textarea(
                            label="Additional details (optional)",
                            placeholder="Any additional information about the issue..."
                        ).classes("w-full").props("rows=3")

                        def create_client_ticket():
                            symptom_id = symptom_select.value
                            if not symptom_id:
                                ui.notify("Please select a symptom", type="warning")
                                return
                            
                            # Check for duplicate
                            if _check_duplicate_symptom(unit_id, symptom_id, user['id']):
                                ui.notify("You already reported this symptom within the last 24 hours", type="warning")
                                log_user_action(f"Blocked duplicate ticket", f"Unit {unit_id}, Symptom {symptom_id}")
                                return
                            
                            # Create ticket
                            symptom = next((s for s in symptoms if s['id'] == symptom_id), None)
                            ticket_data = {
                                "customer_id": unit_info['customer_id'],
                                "location_id": unit_info['location_id'],
                                "unit_id": unit_id,
                                "title": symptom['title'] if symptom else "Service Request",
                                "description": notes_input.value or "",
                                "priority": "Normal",
                                "status": "Open",
                                "requested_by_login_id": user['id'],
                                "symptom_id": symptom_id,
                            }
                            
                            try:
                                ticket_id = create_service_call(ticket_data)
                                log_user_action(f"Created ticket #{ticket_id}", f"Unit {unit_id}, Symptom {symptom['title']}")
                                ui.notify(f"Service ticket #{ticket_id} created successfully", type="positive")
                                dlg.close()
                            except Exception as e:
                                handle_error(e, "creating service ticket")

                        with ui.row().classes("justify-end w-full gap-2 mt-4"):
                            ui.button("Cancel", on_click=dlg.close).props("flat")
                            ui.button("Create Ticket", on_click=create_client_ticket).props("color=green")

                    elif is_admin_or_tech:
                        # ADMIN/TECH: Technical description
                        ui.label("Technical Issue Description").classes("text-sm font-semibold mt-2")
                        
                        title_input = ui.input(
                            label="Issue Title",
                            placeholder="Brief technical summary"
                        ).classes("w-full mb-2")
                        
                        desc_input = ui.textarea(
                            label="Technical Description",
                            placeholder="Detailed findings, fault codes, measurements..."
                        ).classes("w-full").props("rows=4")
                        
                        priority_select = ui.select(
                            label="Priority",
                            options=["Low", "Normal", "High", "Critical"],
                            value="Normal"
                        ).classes("w-full")

                        def create_tech_ticket():
                            if not title_input.value:
                                ui.notify("Please enter an issue title", type="warning")
                                return
                            
                            ticket_data = {
                                "customer_id": unit_info['customer_id'],
                                "location_id": unit_info['location_id'],
                                "unit_id": unit_id,
                                "title": title_input.value,
                                "description": desc_input.value or "",
                                "priority": priority_select.value,
                                "status": "Open",
                                "requested_by_login_id": user['id'],
                                # No symptom_id for admin/tech tickets
                            }
                            
                            try:
                                ticket_id = create_service_call(ticket_data)
                                log_user_action(f"Created tech ticket #{ticket_id}", f"Unit {unit_id}, Priority {priority_select.value}")
                                ui.notify(f"Service ticket #{ticket_id} created successfully", type="positive")
                                dlg.close()
                            except Exception as e:
                                handle_error(e, "creating technical service ticket")

                        with ui.row().classes("justify-end w-full gap-2 mt-4"):
                            ui.button("Cancel", on_click=dlg.close).props("flat")
                            ui.button("Create Ticket", on_click=create_tech_ticket).props("color=green")
                    else:
                        ui.label("You do not have permission to create tickets").classes("text-sm text-red-400")

                # Close button for ticket-exists case
                if open_ticket:
                    with ui.row().classes("justify-end w-full mt-4"):
                        ui.button("Close", on_click=dlg.close).props("flat")

        dlg.open()

    except Exception as exc:
        handle_error(exc, "displaying unit dialog", notify_user=True)
