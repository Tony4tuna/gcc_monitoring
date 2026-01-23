# pages/dashboard.py
# Junior-friendly complete dashboard:
# - ADMIN/TECH: show ONLY warning/alarm units across all customers, grouped by Customer → Location → Unit
# - CLIENT: show their units (you can decide later if client sees only warnings or all)
# - Right side: Service Tickets grid (Open/Closed/All)
# - Top summary cards are symmetric

from __future__ import annotations

from nicegui import ui
from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import json
import smtplib
from email.message import EmailMessage

from core.auth import require_login, current_user, logout
from core.db import get_conn
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts
from core.stats import get_summary_counts
from ui.layout import layout


# ---------------------------------------------------------
# Helpers (simple + safe)
# ---------------------------------------------------------

def _now() -> datetime:
    return datetime.now()

def _generate_ticket_no(service_call_id: int) -> str:
    """Generate ticket number in format YYYYMMDD-####"""
    return f"{_now().strftime('%Y%m%d')}-{service_call_id:04d}"

def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default

def _trim(s: str, max_len: int = 80) -> str:
    s = (s or "").strip()
    return s if len(s) <= max_len else (s[: max_len - 1].rstrip() + "…")

def _as_bool(v: Any, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default

def _get_customer_filter_for_user() -> Optional[int]:
    """
    If user is a CLIENT (hierarchy=4), they can only see their customer_id.
    """
    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)
    if hierarchy == 4:
        return user.get("customer_id")
    return None

def _build_location_text(row: dict) -> str:
    parts = []
    if row.get("location"):
        parts.append(str(row.get("location")))
    city = (row.get("location_city") or "").strip()
    st = (row.get("location_state") or "").strip()
    zp = (row.get("location_zip") or "").strip()
    cs = ", ".join([p for p in [city, st] if p])
    if cs:
        if zp:
            cs = f"{cs} {zp}"
        parts.append(cs)
    return ", ".join([p for p in parts if p]).strip() or "—"


# ---------------------------------------------------------
# DB Queries
# ---------------------------------------------------------

def get_unit_stats(customer_id: Optional[int] = None) -> dict:
    """
    Pulls last reading per unit, plus customer + location.
    Returns:
      units: list of sqlite rows
      health_data: dict[unit_id] => {score,status,issues}
      counts: online/warn/fault + alerts_count
    """
    conn = get_conn()
    try:
        cursor = conn.cursor()

        filters = [
            """
            ur.reading_id IN (
                SELECT MAX(reading_id) FROM UnitReadings GROUP BY unit_id
            )
            """
        ]
        params: list = []

        if customer_id is not None:
            filters.append("c.ID = ?")
            params.append(int(customer_id))

        where_clause = "WHERE " + " AND ".join(filters)

        cursor.execute(f"""
            SELECT
                u.unit_id,
                u.make,
                u.model,
                ur.mode,
                ur.supply_temp,
                ur.return_temp,
                ur.delta_t,
                ur.discharge_psi,
                ur.suction_psi,
                ur.superheat,
                ur.subcooling,
                ur.fault_code,
                ur.unit_status,
                ur.ts,
                ur.v_1,
                ur.v_2,
                ur.v_3,
                ur.compressor_amps,
                pl.ID as location_id,
                pl.address1 as location,
                pl.city as location_city,
                pl.state as location_state,
                pl.zip as location_zip,
                c.company as customer,
                c.email as customer_email,
                c.phone1 as customer_phone,
                c.ID as customer_id
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            {where_clause}
            ORDER BY c.company, pl.address1, u.unit_id
        """, tuple(params))

        units = cursor.fetchall()

        online_count = 0
        warning_count = 0
        fault_count = 0
        temps: list[float] = []
        alerts_count = 0
        health_data: dict[int, dict] = {}

        for row in units:
            reading = dict(row)

            health = calculate_equipment_health_score(reading)
            unit_alerts = evaluate_all_alerts(reading)
            alerts_count += int(unit_alerts.get("count", 0) or 0)

            uid = int(row["unit_id"])
            health_data[uid] = {
                "score": int(health.get("score", 0) or 0),
                "status": health.get("status", "Unknown"),
                "issues": health.get("issues", []),
            }

            score = int(health_data[uid]["score"] or 0)
            if score >= 80:
                online_count += 1
            elif score >= 60:
                warning_count += 1
            else:
                fault_count += 1

            temps.append(float(row["supply_temp"]) if row["supply_temp"] else 0.0)

        avg_temp = int(sum(temps) / len(temps)) if temps else 0

        return {
            "units": units,
            "online_count": online_count,
            "warning_count": warning_count,
            "fault_count": fault_count,
            "avg_temp": avg_temp,
            "alerts_count": alerts_count,
            "health_data": health_data,
        }
    finally:
        conn.close()


# ---------------------------------------------------------
# Service Tickets (grid on the right side)
# ---------------------------------------------------------

def db_list_service_calls(status_filter: str = "Open", customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns tickets across all customers/locations/units.
    If customer_id is provided, filters to that customer.
    status_filter: "Open", "Closed", "All"
    """
    conn = get_conn()
    try:
        where = []
        params: List[Any] = []

        if status_filter in ("Open", "Closed"):
            where.append("sc.status = ?")
            params.append(status_filter)

        if customer_id:
            where.append("sc.customer_id = ?")
            params.append(int(customer_id))

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        rows = conn.execute(f"""
            SELECT
                sc.ID,
                sc.created,
                sc.status,
                sc.priority,
                sc.title,
                sc.description,
                sc.materials_services,
                sc.labor_description,
                sc.customer_id,
                sc.location_id,
                sc.unit_id,
                c.company AS customer,
                pl.address1 AS location,
                u.make,
                u.model,
                u.serial,
                u.equipment_type,
                u.refrigerant_type,
                u.voltage,
                u.amperage,
                u.btu_rating,
                u.tonnage,
                u.breaker_size,
                u.inst_date,
                u.warranty_end_date
            FROM ServiceCalls sc
            LEFT JOIN Customers c ON c.ID = sc.customer_id
            LEFT JOIN PropertyLocations pl ON pl.ID = sc.location_id
            LEFT JOIN Units u ON u.unit_id = sc.unit_id
            {where_sql}
            ORDER BY sc.created DESC
            LIMIT 400
        """, tuple(params)).fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()


def db_update_service_call_status(service_call_id: int, new_status: str) -> None:
    conn = get_conn()
    try:
        if new_status == "Closed":
            conn.execute(
                "UPDATE ServiceCalls SET status = ?, closed = datetime('now') WHERE ID = ?",
                (new_status, int(service_call_id)),
            )
        elif new_status == "Open":
            conn.execute(
                "UPDATE ServiceCalls SET status = ?, closed = NULL WHERE ID = ?",
                (new_status, int(service_call_id)),
            )
        else:
            conn.execute(
                "UPDATE ServiceCalls SET status = ? WHERE ID = ?",
                (new_status, int(service_call_id)),
            )
        conn.commit()
    finally:
        conn.close()


def show_close_dialog_dashboard(call_id: int, on_closed: callable) -> None:
    """Dashboard version of close dialog with reason selection"""
    close_reasons = [
        "Fixed - Issue Resolved",
        "Customer Cancelled",
        "No Access to Equipment",
        "Parts on Order",
        "Warranty Work",
        "Duplicate Call",
        "Unable to Reproduce",
        "Other"
    ]
    
    with ui.dialog(value=True) as dlg:
        with ui.card().classes("gcc-card p-4 w-full max-w-md"):
            ui.label("Close Service Call").classes("text-lg font-bold")
            ui.label("Select reason for closing:").classes("text-sm gcc-muted mb-3")
            
            reason_select = ui.select(
                {r: r for r in close_reasons},
                label="Close Reason"
            ).props("outlined dense").classes("w-full")
            
            ui.label("Additional Notes (optional)").classes("text-sm font-bold mt-3")
            notes_area = ui.textarea(
                label="Notes"
            ).props("outlined dense autogrow").classes("w-full")
            
            def submit_close():
                reason = reason_select.value
                if not reason:
                    ui.notify("Please select a reason", type="warning")
                    return
                
                notes = notes_area.value or ""
                close_note = f"[CLOSED: {reason}]"
                if notes:
                    close_note += f"\n{notes}"
                
                conn = get_conn()
                try:
                    conn.execute(
                        "UPDATE ServiceCalls SET status = ?, description = ?, closed = datetime('now') WHERE ID = ?",
                        ("Closed", close_note, int(call_id))
                    )
                    conn.commit()
                finally:
                    conn.close()
                
                ui.notify(f"Call {call_id} closed", type="positive")
                dlg.close()
                on_closed()
            
            with ui.row().classes("justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dlg.close).props("flat")
                ui.button("Close Call", on_click=submit_close).props("color=green")


def _require_reportlab():
    """Check if reportlab is installed"""
    try:
        import reportlab
    except ImportError:
        raise ImportError("reportlab library required. Install with: pip install reportlab")


def generate_service_order_pdf(ticket_no: str, data: dict, health: dict, alerts: dict, company: dict,
                               out_dir: str = "reports/service_orders") -> tuple:
    """Generate PDF service order with requested layout."""
    _require_reportlab()

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    os.makedirs(out_dir, exist_ok=True)
    unit_id = int(data.get("unit_id") or 0)
    unit_name = f"RTU-{unit_id}" if unit_id else "RTU"
    filename = f"ServiceOrder_{ticket_no}_{unit_name}.pdf"
    pdf_path = os.path.join(out_dir, filename)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    w, h = letter
    left = 40
    right = w - 40
    y = h - 46

    def text(x, y, s, size=10, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, s)

    def draw_box_with_lines(title: str, y_top: float, height: float, content: str = "") -> float:
        """Draw labeled box with writing lines and optional content."""
        text(left, y_top, title, 10, True)
        y_inner = y_top - 14
        c.saveState()
        c.setLineWidth(0.6)
        c.setStrokeColor(colors.lightgrey)
        c.rect(left, y_inner - height, right - left, height, stroke=1, fill=0)
        line_y = y_inner - 12
        while line_y > (y_inner - height + 12):
            c.line(left + 10, line_y, right - 10, line_y)
            line_y -= 14
        c.restoreState()
        if content:
            text(left + 12, y_inner - 10, content[:200], 9)
            if len(content) > 200:
                text(left + 12, y_inner - 24, content[200:400], 9)
        return y_inner - height - 16

    # Company info: name, address, city/state/zip, phone, general email
    comp_name = company.get("company") or company.get("name") or "Company"
    comp_address = company.get("address1") or ""
    comp_city_line = " ".join([p for p in [
        (company.get("city") or "").strip(),
        (company.get("state") or "").strip(),
        (company.get("zip") or "").strip()
    ] if p]).strip()
    comp_phone = company.get("phone") or ""
    comp_email = company.get("email") or ""  # General company email (left side)
    
    # Format phone as (xxx) xxx-xxxx
    import re
    if comp_phone:
        digits = re.sub(r'\D', '', comp_phone)
        if len(digits) == 10:
            comp_phone = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            comp_phone = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    
    text(left, y, comp_name, 10, True)
    y_head = y - 12
    if comp_address:
        text(left, y_head, comp_address, 9)
        y_head -= 12
    if comp_city_line:
        text(left, y_head, comp_city_line, 9)
        y_head -= 12
    if comp_phone:
        text(left, y_head, comp_phone, 9)
        y_head -= 12
    if comp_email:
        text(left, y_head, comp_email, 9)
        y_head -= 12

    dt = datetime.now()
    # Right side: Service Ticket, Ticket #, Date, Time, License #, Service Email
    comp_license = company.get("business_license") or ""
    comp_service_email = company.get("service_email") or ""
    
    ticket_block = [
        ("Service Ticket", True),
        (f"Ticket #: {ticket_no}", False),
        (f"Date: {dt.date()}", False),
        (f"Time: {dt.strftime('%H:%M:%S')}", False)
    ]
    if comp_license:
        ticket_block.append((f"License #: {comp_license}", False))
    if comp_service_email:
        ticket_block.append((f"Service: {comp_service_email}", False))
    
    tb_y = y
    for line, bold in ticket_block:
        width = c.stringWidth(line, "Helvetica-Bold" if bold else "Helvetica", 10 if bold else 9)
        x_pos = right - width
        text(x_pos, tb_y, line, 10 if bold else 9, bold=bold)
        tb_y -= 12

    y = min(y_head, tb_y) - 10
    c.line(left, y, right, y)
    y -= 16

    mid = (left + right) / 2

    lx = left
    rx = mid + 8
    text(lx, y, "Client / Location", 10, True)
    text(rx, y, "Service Status", 10, True)
    y -= 12

    text(lx, y, f"Customer: {data.get('customer', '—')}", 9); y -= 12
    text(lx, y, f"Location: {data.get('location', '—')}", 9); y -= 14

    y_status = y + 26
    text(rx, y_status, f"Status: {data.get('status', '—')}", 9); y_status -= 12
    text(rx, y_status, f"Priority: {data.get('priority', '—')}", 9); y_status -= 12
    text(rx, y_status, f"Created: {(data.get('created') or '')[:19]}", 9)

    y -= 8
    c.line(left, y, right, y)
    y -= 14
    
    # Unit Information section (two columns)
    text(left, y, "Unit Information", 10, True)
    y_unit = y - 12
    unit_id = data.get('unit_id', 0)
    eq_type = data.get('equipment_type', 'RTU')
    text(left, y_unit, f"Unit: {eq_type}-{unit_id}" if unit_id else "Unit: —", 9); y_unit -= 12
    text(left, y_unit, f"Make: {data.get('make', '—')}", 9); y_unit -= 12
    text(left, y_unit, f"Model: {data.get('model', '—')}", 9); y_unit -= 12
    text(left, y_unit, f"Serial: {data.get('serial', '—')}", 9); y_unit -= 12
    text(left, y_unit, f"Installed: {data.get('inst_date', '—')}", 9); y_unit -= 12
    text(left, y_unit, f"Warranty: {data.get('warranty_end_date', '—')}", 9)
    
    # Right side: Technical specifications
    y_specs = y - 12
    text(rx, y_specs, f"Capacity: {data.get('tonnage', '—')} / {data.get('btu_rating', '—')}", 9); y_specs -= 12
    text(rx, y_specs, f"Refrigerant: {data.get('refrigerant_type', '—')}", 9); y_specs -= 12
    text(rx, y_specs, f"Voltage: {data.get('voltage', '—')}", 9); y_specs -= 12
    text(rx, y_specs, f"Amperage: {data.get('amperage', '—')}", 9); y_specs -= 12
    text(rx, y_specs, f"Breaker: {data.get('breaker_size', '—')}", 9)
    
    y = min(y_unit, y_specs) - 14
    
    c.line(left, y, right, y)
    y -= 18

    y = draw_box_with_lines("Materials", y, 160, content=(data.get("materials_services") or ""))
    c.line(left, y, right, y)
    y -= 18

    y = draw_box_with_lines("Labor", y, 160, content=(data.get("labor_description") or ""))

    # Signature near bottom
    sig_y = 60
    text(left, sig_y, "Customer Signature: ____________________________", 9)
    text(right - 150, sig_y, "Date: ____________", 9)

    c.showPage()
    c.save()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    if not pdf_bytes or len(pdf_bytes) < 500:
        raise RuntimeError(f"PDF generation failed (too small): {pdf_path} ({len(pdf_bytes)} bytes)")

    return pdf_path, pdf_bytes


def show_print_ticket_dashboard(ticket: Dict[str, Any]) -> None:
    """Dashboard version - generate actual PDF file"""
    try:
        # Prepare data dict
        data = {
            "customer": ticket.get('customer', '—'),
            "location": ticket.get('location', '—'),
            "customer_phone": "—",
            "customer_email": "—",
            "unit_id": ticket.get('unit_id', 0),
            "equipment_type": ticket.get('equipment_type', 'RTU'),
            "make": ticket.get('make', '—'),
            "model": ticket.get('model', '—'),
            "serial": ticket.get('serial', '—'),
            "refrigerant_type": ticket.get('refrigerant_type', '—'),
            "voltage": ticket.get('voltage', '—'),
            "amperage": ticket.get('amperage', '—'),
            "btu_rating": ticket.get('btu_rating', '—'),
            "tonnage": ticket.get('tonnage', '—'),
            "breaker_size": ticket.get('breaker_size', '—'),
            "inst_date": ticket.get('inst_date', '—'),
            "warranty_end_date": ticket.get('warranty_end_date', '—'),
            "status": ticket.get('status', '—'),
            "priority": ticket.get('priority', '—'),
            "title": ticket.get('title', '—'),
            "description": ticket.get('description', '—'),
            "materials_services": ticket.get('materials_services', '—'),
            "labor_description": ticket.get('labor_description', '—'),
            "created": ticket.get('created', ''),
        }
        
        health = {
            "score": 85,
            "status": "Good"
        }
        
        alerts = {
            "alerts": []
        }

        # Pull company profile from DB if available (CompanyProfile or CompanyInfo), else fall back
        company = {
            "company": "GCC TECHNOLOGY",
            "address1": "123 Tech Street",
            "address2": "",
            "city": "Tech City",
            "state": "TC",
            "zip": "12345",
            "phone": "(555) 123-4567",
            "email": "support@gcc.com",
            "website": "www.gcc.com"
        }
        conn = get_conn()
        try:
            row = conn.execute("SELECT * FROM CompanyProfile LIMIT 1").fetchone()
            if row is None:
                row = conn.execute("SELECT * FROM CompanyInfo LIMIT 1").fetchone()
            if row:
                row = dict(row)
                company = {
                    "company": row.get("company_name") or row.get("name") or row.get("company") or company["company"],
                    "address1": row.get("address1") or "",
                    "address2": row.get("address2") or "",
                    "city": row.get("city") or "",
                    "state": row.get("state") or "",
                    "zip": row.get("zip") or "",
                    "phone": row.get("phone") or row.get("fax") or company.get("phone"),
                    "email": row.get("email") or company.get("email"),
                    "service_email": row.get("service_email") or row.get("email") or "",
                    "business_license": row.get("business_license") or "",
                    "website": row.get("website") or company.get("website"),
                }
        except Exception:
            pass
        finally:
            conn.close()
        
        ticket_no = _generate_ticket_no(ticket.get('ID', 0))
        pdf_path, pdf_bytes = generate_service_order_pdf(ticket_no, data, health, alerts, company)
        
        # Download the PDF
        ui.download(pdf_bytes, filename=os.path.basename(pdf_path))
        ui.notify(f"PDF generated: {os.path.basename(pdf_path)}", type="positive")
        
    except Exception as e:
        ui.notify(f"PDF generation failed: {str(e)}", type="negative")


def confirm_delete_dashboard(call_id: int, on_deleted: callable) -> None:
    """Dashboard version of delete confirmation"""
    confirmed = {"value": False}
    
    with ui.dialog(value=True) as dlg:
        with ui.card().classes("gcc-card p-4 w-full max-w-md"):
            ui.label("Delete Service Call?").classes("text-lg font-bold text-red-500")
            ui.label(f"This will permanently delete call #{call_id}").classes("text-sm gcc-muted mb-3")
            ui.label("This action cannot be undone.").classes("text-sm text-red-400 font-bold mb-4")
            
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.checkbox(text="Yes, I confirm deletion", on_change=lambda e: confirmed.__setitem__("value", e.value))
            
            def submit_delete():
                if not confirmed["value"]:
                    ui.notify("Please confirm deletion", type="warning")
                    return
                
                conn = get_conn()
                try:
                    conn.execute("DELETE FROM ServiceCalls WHERE ID = ?", (int(call_id),))
                    conn.commit()
                finally:
                    conn.close()
                
                ui.notify(f"Call {call_id} deleted", type="positive")
                dlg.close()
                on_deleted()
            
            with ui.row().classes("justify-end gap-2"):
                ui.button("Cancel", on_click=dlg.close).props("flat")
                ui.button("Delete", on_click=submit_delete).props("color=red")


def ui_show_ticket_dialog(ticket: Dict[str, Any]) -> None:
    with ui.dialog(value=True) as dlg:
        with ui.card().classes("gcc-card p-4 w-full max-w-4xl"):
            ui.label(f"Service Ticket #{ticket['ID']}").classes("text-lg font-bold")
            ui.label(
                f"Status: {ticket.get('status','—')} | Priority: {ticket.get('priority','—')} | Created: {(ticket.get('created') or '')[:19]}"
            ).classes("text-sm gcc-muted")

            ui.separator().classes("my-2")

            ui.label(f"Customer: {ticket.get('customer','—')}").classes("text-sm")
            ui.label(f"Location: {ticket.get('location','—')}").classes("text-sm")
            
            eq_type = ticket.get('equipment_type', 'RTU')
            unit_txt = f"{eq_type}-{ticket.get('unit_id')}" if ticket.get("unit_id") else "—"
            ui.label(f"Unit: {unit_txt}").classes("text-sm")
            
            # Equipment specs
            specs = []
            if ticket.get('make'):
                specs.append(f"Make: {ticket.get('make')}")
            if ticket.get('model'):
                specs.append(f"Model: {ticket.get('model')}")
            if ticket.get('refrigerant_type'):
                specs.append(f"Refrig: {ticket.get('refrigerant_type')}")
            if ticket.get('tonnage'):
                specs.append(f"Capacity: {ticket.get('tonnage')} Ton")
            if specs:
                ui.label(" | ".join(specs)).classes("text-sm gcc-muted")

            ui.separator().classes("my-2")

            ui.label("Title").classes("text-sm font-bold")
            ui.label(ticket.get("title") or "—").classes("text-sm")

            ui.separator().classes("my-2")

            ui.label("General Description").classes("text-sm font-bold")
            ui.textarea(value=ticket.get("description") or "").props("readonly autogrow").classes("w-full")

            ui.separator().classes("my-2")

            ui.label("Materials & Services").classes("text-sm font-bold")
            ui.textarea(value=ticket.get("materials_services") or "").props("readonly autogrow").classes("w-full")

            ui.separator().classes("my-2")

            ui.label("Labor Description").classes("text-sm font-bold")
            ui.textarea(value=ticket.get("labor_description") or "").props("readonly autogrow").classes("w-full")

            with ui.row().classes("justify-end mt-3 gap-2"):
                ui.button("Close", on_click=dlg.close).props("dense")


def render_service_tickets_panel(customer_id: Optional[int]) -> None:
    """Render service tickets panel with professional card layout matching tickets.py"""
    ui.label("Service Tickets").classes("text-lg font-bold")
    ui.label("Open / Closed tickets").classes("text-xs gcc-muted mb-2")

    state = {"status": "Open"}
    
    container = ui.column().classes("w-full gap-3")
    
    def refresh_tickets() -> None:
        container.clear()
        
        # Filter bar
        with container:
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.select(
                    {"Open": "Open", "Closed": "Closed", "All": "All"},
                    value=state["status"],
                    label="Show",
                    on_change=lambda e: (state.__setitem__("status", e.value), refresh_tickets()),
                ).props("dense outlined").classes("w-36")
                ui.button("Refresh", on_click=refresh_tickets).props("outline dense")
            
            # Get tickets
            tickets = db_list_service_calls(status_filter=state["status"], customer_id=customer_id)
            
            if not tickets:
                ui.label("No service calls").classes("gcc-muted")
            else:
                for call in tickets:
                    call_id = call["ID"]
                    status = call.get("status", "—")
                    priority = call.get("priority", "—")
                    
                    with ui.card().classes("gcc-card p-3 border-l-4 border-blue-500"):
                        # Header row
                        with ui.row().classes("items-center justify-between mb-2"):
                            ui.label(f"#{call_id} - {call.get('title', 'Untitled')}").classes("text-sm font-bold flex-1")
                            ui.label(f"{status} | {priority}").classes("text-xs")
                        
                        # Details row
                        with ui.grid(columns=4).classes("gap-2 text-xs mb-3"):
                            ui.label(f"Customer: {call.get('customer', 'N/A')}")
                            ui.label(f"Location: {call.get('location', 'N/A')}")
                            eq_type = call.get('equipment_type', 'RTU')
                            unit_txt = f"{eq_type}-{call.get('unit_id')}" if call.get('unit_id') else "—"
                            ui.label(f"Unit: {unit_txt}")
                            specs_txt = ""
                            if call.get('tonnage'):
                                specs_txt += f"{call.get('tonnage')}T "
                            if call.get('refrigerant_type'):
                                specs_txt += f"{call.get('refrigerant_type')}"
                            ui.label(f"Specs: {specs_txt.strip() or 'N/A'}")
                            ui.label(f"Created: {(call.get('created') or '')[:10]}")
                        
                        # Actions row
                        with ui.row().classes("justify-end gap-1"):
                            # Print button (always)
                            ui.button(icon="print", on_click=lambda c=call: show_print_ticket_dashboard(c)).props("flat dense color=blue")
                            
                            # Edit button (always)
                            ui.button(icon="edit", on_click=lambda c=call: ui_show_ticket_dialog(c)).props("flat dense")
                            
                            # Close button (if not closed)
                            if status != "Closed":
                                ui.button(icon="check_circle", on_click=lambda cid=call_id: show_close_dialog_dashboard(cid, refresh_tickets)).props("flat dense color=green")
                            
                            # Delete button (only if closed)
                            if status == "Closed":
                                ui.button(icon="delete", on_click=lambda cid=call_id: confirm_delete_dashboard(cid, refresh_tickets)).props("flat dense color=red")
    
    refresh_tickets()


# ---------------------------------------------------------
# Dashboard UI (Left side: failing units grouped)
# ---------------------------------------------------------

def render_top_cards(stats: dict) -> None:
    summary = get_summary_counts()

    # Symmetric cards: same padding + centered
    # Use 4 columns always; if you want responsive later we can do that too
    with ui.grid(columns=4).classes("gap-3 w-full"):
        def card(title: str, value: str, extra_classes: str = ""):
            with ui.card().classes(f"gcc-card p-4 text-center min-h-[92px] {extra_classes}"):
                ui.label(title).classes("text-xs gcc-muted")
                ui.label(value).classes("text-2xl font-bold")

        card("Clients", str(summary.get("clients", 0)))
        card("Locations", str(summary.get("locations", 0)))
        card("Equipment", str(summary.get("equipment", 0)))
        card("Alerts (latest)", str(stats.get("alerts_count", 0)), "text-yellow-400")


def _is_warning_or_alarm(score: int, fault_code: Any) -> bool:
    """
    Rules:
      - Warning: 60-79
      - Alarm: 0-59
      - Also treat any fault_code as problem
    """
    if fault_code and str(fault_code).strip() and str(fault_code).strip() not in ("—", "None", "0"):
        return True
    return score < 80


def render_failing_units_grouped(stats: dict, admin_mode: bool) -> None:
    """
    Admin mode: show ONLY warning/alarm units.
    Client mode: you can decide:
      - show all units, OR
      - show only warning/alarm.
    For now:
      - Admin: only warning/alarm
      - Client: show all (more useful for the client)
    """
    units = [dict(u) for u in stats.get("units", [])]
    health_data = stats.get("health_data", {})

    # Build list with health score attached
    enriched: List[Dict[str, Any]] = []
    for u in units:
        uid = int(u.get("unit_id") or 0)
        health = health_data.get(uid, {})
        score = int(health.get("score", 0) or 0)
        u["_score"] = score
        u["_status"] = health.get("status", "Unknown")
        enriched.append(u)

    # Filter for admin
    if admin_mode:
        enriched = [u for u in enriched if _is_warning_or_alarm(int(u["_score"]), u.get("fault_code"))]

    # Nothing to show?
    if not enriched:
        ui.label("No warnings or alarms right now.").classes("gcc-muted")
        return

    # Group: customer → location
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for u in enriched:
        cust = (u.get("customer") or "—").strip()
        loc = (u.get("location") or "—").strip()
        grouped.setdefault(cust, {}).setdefault(loc, []).append(u)

    # UI
    title = "Units With Warnings/Alarms" if admin_mode else "My Units"
    ui.label(title).classes("text-lg font-bold")
    ui.label("Grouped by Customer → Location").classes("text-xs gcc-muted mb-2")

    # Customer expansions
    for cust_name in grouped.keys():
        cust_locations = grouped[cust_name]
        with ui.expansion(f"{cust_name}  ({sum(len(v) for v in cust_locations.values())} units)", value=True).classes("gcc-card w-full"):
            for loc_name in cust_locations.keys():
                loc_units = cust_locations[loc_name]
                with ui.expansion(f"{loc_name}  ({len(loc_units)} units)", value=False).classes("w-full"):
                    # Compact grid - 6 columns for information density
                    with ui.grid(columns=6).classes("gap-2 w-full"):
                        for u in loc_units:
                            uid = int(u.get("unit_id") or 0)
                            score = int(u.get("_score") or 0)
                            
                            # Color by health score
                            if score < 60:
                                card_class = "bg-red-900 border-l-4 border-red-500"
                                score_text = "text-red-300"
                            elif score < 80:
                                card_class = "bg-orange-900 border-l-4 border-orange-500"
                                score_text = "text-orange-300"
                            else:
                                card_class = "bg-green-900 border-l-4 border-green-500"
                                score_text = "text-green-300"

                            with ui.card().classes(f"gcc-card p-2 w-full {card_class}"):
                                # Row 1: Unit ID + Score
                                with ui.row().classes("items-center justify-between gap-1 mb-1"):
                                    eq_type = u.get('equipment_type', 'RTU')
                                    ui.label(f"{eq_type}-{uid}").classes("text-xs font-bold flex-1 truncate")
                                    ui.label(f"{score}%").classes(f"text-xs font-bold {score_text}")
                                
                                # Row 2: Make/Model (compact)
                                make = (u.get('make') or '').strip()[:5]
                                model = (u.get('model') or '').strip()[:5]
                                if make or model:
                                    ui.label(f"{make} {model}".strip()).classes("text-xs text-gray-300 truncate")
                                
                                # Row 3: Specs (inline, compact)
                                specs = []
                                if u.get('refrigerant_type'):
                                    specs.append(u.get('refrigerant_type')[:6])
                                if u.get('tonnage'):
                                    specs.append(f"{u.get('tonnage')}T")
                                if specs:
                                    ui.label(" • ".join(specs)).classes("text-xs text-gray-400 truncate")
                                
                                # Row 4: Status + Temp (inline)
                                mode = (u.get('mode') or '—')[:3]
                                temp = f"{u.get('supply_temp')}°F" if u.get('supply_temp') else ""
                                status_line = f"{mode} | {temp}" if temp else mode
                                ui.label(status_line).classes("text-xs font-semibold text-blue-300 truncate")
                                fault = (u.get('fault_code') or '—')
                                ui.label(f"Fault: {fault}").classes("text-xs")

                                with ui.row().classes("justify-end mt-2"):
                                    ui.button("Details", on_click=lambda uid=uid: ui.navigate.to(f"/equipment?unit={uid}")).props("dense outline")


# ---------------------------------------------------------
# Shared dashboard renderer (used by main dashboard and client portal)
# ---------------------------------------------------------

def render_dashboard(customer_id: Optional[int] = None) -> None:
    """Render the dashboard body (cards + units + tickets)."""
    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)
    admin_mode = (hierarchy != 4)

    stats = get_unit_stats(customer_id=int(customer_id)) if customer_id else get_unit_stats(customer_id=None)

    # Top summary cards
    render_top_cards(stats)

    # **PRIORITY: Units With Warnings/Alarms at the top**
    render_failing_units_grouped(stats, admin_mode=admin_mode)

    # Bottom section: Service Tickets (full width)
    with ui.column().classes("w-full gap-3 mt-8"):
        ticket_customer_filter = None if admin_mode else int(customer_id or 0) or None
        render_service_tickets_panel(ticket_customer_filter)


# ---------------------------------------------------------
# Page Entrypoint
# ---------------------------------------------------------

def page():
    if not require_login():
        return

    user = current_user() or {}
    hierarchy = int(user.get("hierarchy", 5) or 5)

    customer_filter = _get_customer_filter_for_user()

    # Prevent clients from viewing all customers if their account lacks a customer_id
    if hierarchy == 4 and not customer_filter:
        ui.notify("No customer assigned to your account. Contact support.", type="negative")
        ui.navigate.to("/login")
        return

    # Admin/Tech mode if NOT client
    admin_mode = (hierarchy != 4)

    with layout("HVAC Dashboard", show_logout=True):
        render_dashboard(customer_id=customer_filter if admin_mode else int(customer_filter or 0) or None)
