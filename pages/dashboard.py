# pages/dashboard.py
from __future__ import annotations

from nicegui import ui
from typing import Optional

from core.auth import require_login, current_user
from core.db import get_conn
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts
from core.stats import get_summary_counts
from core.version import get_version, get_build_info
from ui.layout import layout
from ui.unit_issue_dialog import open_unit_issue_dialog
from core.logger import log_user_action, handle_error, with_error_handling


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _get_customer_filter_for_user() -> Optional[int]:
    user = current_user() or {}
    if int(user.get("hierarchy", 5)) == 4:
        return user.get("customer_id")
    return None


# ---------------------------------------------------------
# DATA
# ---------------------------------------------------------

@with_error_handling("loading unit stats")
def get_unit_stats(customer_id: Optional[int] = None) -> dict:
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
        params = []

        if customer_id:
            filters.append("c.ID = ?")
            params.append(int(customer_id))

        where_sql = "WHERE " + " AND ".join(filters)

        rows = cursor.execute(
            f"""
            SELECT
                u.unit_id,
                u.make,
                u.model,
                ur.mode,
                ur.supply_temp,
                ur.fault_code,
                pl.address1 AS location,
                c.company AS customer,
                c.ID as customer_id
            FROM UnitReadings ur
            JOIN Units u ON ur.unit_id = u.unit_id
            JOIN PropertyLocations pl ON u.location_id = pl.ID
            JOIN Customers c ON pl.customer_id = c.ID
            {where_sql}
            ORDER BY c.company, pl.address1, u.unit_id
            """,
            tuple(params),
        ).fetchall()

        units = []
        health_data = {}
        alerts_count = 0

        for r in rows:
            row = dict(r)
            health = calculate_equipment_health_score(row)
            alerts = evaluate_all_alerts(row)

            uid = row["unit_id"]
            health_data[uid] = {
                "score": int(health.get("score", 0)),
                "status": health.get("status", "Unknown"),
            }
            alerts_count += int(alerts.get("count", 0))
            units.append(row)

        return {
            "units": units,
            "health_data": health_data,
            "alerts_count": alerts_count,
        }
    finally:
        conn.close()


@with_error_handling("loading tickets status")
def get_tickets_status(customer_id: Optional[int] = None) -> dict:
    """Get open tickets mapped by unit_id"""
    conn = get_conn()
    try:
        where_parts = ["sc.status IN ('Open', 'OPEN', 'Pending', 'In Progress')"]
        params = []
        
        if customer_id:
            where_parts.append("sc.customer_id = ?")
            params.append(customer_id)
        
        where_sql = "WHERE " + " AND ".join(where_parts)
        
        rows = conn.execute(
            f"""
            SELECT 
                sc.unit_id,
                sc.ID as ticket_id,
                sc.ticket_no,
                sc.status,
                sc.created,
                sc.requested_by_login_id,
                l.hierarchy
            FROM ServiceCalls sc
            LEFT JOIN Logins l ON sc.requested_by_login_id = l.ID
            {where_sql}
            ORDER BY sc.created DESC
            """,
            tuple(params)
        ).fetchall()
        
        # Map unit_id -> ticket info (most recent)
        tickets_by_unit = {}
        for row in rows:
            r = dict(row)
            uid = r['unit_id']
            if uid not in tickets_by_unit:
                tickets_by_unit[uid] = {
                    'ticket_id': r['ticket_id'],
                    'ticket_no': r['ticket_no'],
                    'status': r['status'],
                    'created': r['created'],
                    'is_client': r['hierarchy'] == 4 if r['hierarchy'] else False
                }
        
        return tickets_by_unit
    finally:
        conn.close()


@with_error_handling("loading open tickets")
def get_open_tickets(customer_id: Optional[int] = None):
    """Get all open tickets for the tickets grid"""
    conn = get_conn()
    try:
        where_parts = ["sc.status IN ('Open', 'OPEN', 'Pending', 'In Progress')"]
        params = []
        
        if customer_id:
            where_parts.append("sc.customer_id = ?")
            params.append(customer_id)
        
        where_sql = "WHERE " + " AND ".join(where_parts)
        
        rows = conn.execute(
            f"""
            SELECT 
                sc.ID,
                sc.ticket_no,
                sc.unit_id,
                sc.status,
                sc.priority,
                sc.title,
                sc.created,
                sc.requested_by_login_id,
                c.company as customer,
                pl.address1 as location,
                l.hierarchy,
                l.login_id as created_by_email
            FROM ServiceCalls sc
            LEFT JOIN Customers c ON sc.customer_id = c.ID
            LEFT JOIN PropertyLocations pl ON sc.location_id = pl.ID
            LEFT JOIN Logins l ON sc.requested_by_login_id = l.ID
            {where_sql}
            ORDER BY sc.created DESC
            LIMIT 50
            """,
            tuple(params)
        ).fetchall()
        
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------
# TOP CARDS
# ---------------------------------------------------------

def render_top_cards(stats: dict) -> None:
    summary = get_summary_counts()

    with ui.grid(columns=4).classes("gap-3 w-full"):

        def card(title: str, value: str):
            with ui.card().classes("gcc-card p-4 text-center"):
                ui.label(title).classes("text-xs gcc-muted")
                ui.label(str(value)).classes("text-2xl font-bold")

        card("Clients", summary.get("clients", 0))
        card("Locations", summary.get("locations", 0))
        card("Equipment", summary.get("equipment", 0))
        card("Alerts", stats.get("alerts_count", 0))


# ---------------------------------------------------------
# ADMIN: UNITS GRID (row-click, reliable)
# ---------------------------------------------------------

def render_admin_units_grid(stats: dict, tickets_by_unit: dict) -> None:
    with ui.element("div").classes("gcc-dashboard-grid-item"):
        ui.label("Units With Warnings / Alarms").classes("text-lg font-bold mb-2")
        ui.label("Click any row to view details or create a service ticket").classes("text-xs gcc-muted mb-2")

        rows = []
        for u in stats["units"]:
            uid = u["unit_id"]
            score = stats["health_data"].get(uid, {}).get("score", 0)

            if score >= 80:
                continue

            ticket_info = tickets_by_unit.get(uid)
            
            if ticket_info:
                ticket_status = f"🎫 {ticket_info['ticket_no'] or f'#{ticket_info["ticket_id"]}'}"
                created_by = "CLIENT" if ticket_info['is_client'] else "TECH"
            else:
                ticket_status = "⚠️ NO TICKET"
                created_by = "—"

            rows.append({
                "customer": (u.get("customer") or "")[:30],
                "location": (u.get("location") or "")[:30],
                "unit": f"RTU-{uid}",
                "score": f"{score}%",
                "ticket": ticket_status,
                "by": created_by,
                "fault": u.get("fault_code") or "—",
                "temp": f"{u.get('supply_temp')}°F" if u.get("supply_temp") is not None else "—",
                "mode": u.get("mode") or "—",
                "unit_id": uid,
            })

        if not rows:
            ui.label("No warnings or alarms right now.").classes("gcc-muted")
            return

        columns = [
            {"name": "customer", "label": "Customer", "field": "customer"},
            {"name": "location", "label": "Location", "field": "location"},
            {"name": "unit", "label": "Unit", "field": "unit"},
            {"name": "score", "label": "Score", "field": "score"},
            {"name": "ticket", "label": "Ticket Status", "field": "ticket"},
            {"name": "by", "label": "By", "field": "by"},
            {"name": "fault", "label": "Fault", "field": "fault"},
            {"name": "temp", "label": "Temp", "field": "temp"},
            {"name": "mode", "label": "Mode", "field": "mode"},
        ]

        table = ui.table(
            columns=columns, 
            rows=rows, 
            row_key="unit_id"
        ).classes("gcc-dashboard-table").props("dense flat virtual-scroll")
        
        # Add custom slot for ticket status column with color coding
        table.add_slot('body-cell-ticket', r'''
            <q-td :props="props">
                <q-badge :color="props.value.includes('NO TICKET') ? 'red' : 'green'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        # Add custom slot for "By" column with color coding
        table.add_slot('body-cell-by', r'''
            <q-td :props="props">
                <q-badge v-if="props.value === 'CLIENT'" color="amber">
                    {{ props.value }}
                </q-badge>
                <q-badge v-else-if="props.value === 'TECH'" color="blue">
                    {{ props.value }}
                </q-badge>
                <span v-else class="text-grey">{{ props.value }}</span>
            </q-td>
        ''')

        def _extract_row_from_args(args):
            """
            NiceGUI row-click args often look like:
              [mouseEventDict, rowDict, rowIndex]
            So the row is usually args[1].
            """
            if isinstance(args, list):
                if len(args) >= 2 and isinstance(args[1], dict):
                    return args[1]
                # fallback: try any dict item
                for item in args:
                    if isinstance(item, dict) and "unit_id" in item:
                        return item
                return None
            if isinstance(args, dict):
                return args
            return None

        def _open_dialog_from_row(e):
            row = _extract_row_from_args(e.args)

            if not row:
                ui.notify("Row click: could not read row data", type="negative")
                return

            unit_id = row.get("unit_id")
            if unit_id is None:
                ui.notify("Row click: unit_id missing", type="negative")
                return

            try:
                unit_id = int(unit_id)
            except Exception:
                ui.notify(f"Row click: bad unit_id {unit_id!r}", type="negative")
                return

            open_unit_issue_dialog(unit_id)

        table.on("row-click", _open_dialog_from_row)


# ---------------------------------------------------------
# OPEN TICKETS GRID
# ---------------------------------------------------------

def render_tickets_grid(customer_id: Optional[int]) -> None:
    tickets = get_open_tickets(customer_id)
    
    with ui.element("div").classes("gcc-dashboard-grid-item"):
        ui.label("Open Service Tickets").classes("text-lg font-bold mb-2")
        ui.label("Click any row to view ticket details").classes("text-xs gcc-muted mb-2")
        
        if not tickets:
            ui.label("No open tickets").classes("gcc-muted")
            return
        
        rows = []
        for t in tickets:
            created_by = "CLIENT" if t.get('hierarchy') == 4 else "TECH/ADMIN"
            
            rows.append({
                "ticket": t.get('ticket_no') or f"#{t['ID']}",
                "customer": (t.get('customer') or "")[:25],
                "location": (t.get('location') or "")[:25],
                "unit": f"RTU-{t['unit_id']}" if t.get('unit_id') else "—",
                "title": (t.get('title') or "")[:40],
                "status": t['status'],
                "priority": t.get('priority') or "Normal",
                "by": created_by,
                "created": t['created'][:16] if t.get('created') else "—",
                "ticket_id": t['ID']
            })
        
        columns = [
            {"name": "ticket", "label": "Ticket", "field": "ticket", "align": "left"},
            {"name": "customer", "label": "Customer", "field": "customer"},
            {"name": "location", "label": "Location", "field": "location"},
            {"name": "unit", "label": "Unit", "field": "unit"},
            {"name": "title", "label": "Issue", "field": "title"},
            {"name": "status", "label": "Status", "field": "status"},
            {"name": "priority", "label": "Priority", "field": "priority"},
            {"name": "by", "label": "Created By", "field": "by"},
            {"name": "created", "label": "Created", "field": "created"},
        ]
        
        table = ui.table(
            columns=columns, 
            rows=rows, 
            row_key="ticket_id"
        ).classes("gcc-dashboard-table").props("dense flat virtual-scroll")
        
        # Color coding for "by" column
        table.add_slot('body-cell-by', r'''
            <q-td :props="props">
                <q-badge :color="props.value === 'CLIENT' ? 'amber' : 'blue'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        # Color coding for priority
        table.add_slot('body-cell-priority', r'''
            <q-td :props="props">
                <q-badge :color="props.value === 'Critical' ? 'red' : props.value === 'High' ? 'orange' : 'grey'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        # Navigate to ticket details on click
        def on_ticket_click(e):
            row = e.args[1] if len(e.args) >= 2 else None
            if row:
                ticket_id = row.get('ticket_id')
                ui.navigate.to(f"/tickets?id={ticket_id}")
        
        table.on("row-click", on_ticket_click)


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

def render_dashboard(customer_id: Optional[int]) -> None:
    user = current_user() or {}
    admin = int(user.get("hierarchy", 5)) != 4

    stats = get_unit_stats(customer_id if not admin else None)
    tickets_by_unit = get_tickets_status(customer_id if not admin else None)

    render_top_cards(stats)

    if admin:
        # Two-column layout: Faulty Units + Open Tickets
        with ui.element("div").classes("gcc-dashboard-grid"):
            render_admin_units_grid(stats, tickets_by_unit)
            render_tickets_grid(customer_id if not admin else None)
    else:
        ui.label("Client dashboard unchanged").classes("gcc-muted")

    with ui.row().classes("text-xs gcc-muted mt-6 justify-center"):
        ui.label(f"GCC Monitoring v{get_version()} • Built {get_build_info().get('build_date','—')}")


# ---------------------------------------------------------
# PAGE
# ---------------------------------------------------------

def page():
    if not require_login():
        return

    log_user_action("Viewed Dashboard")
    customer_filter = _get_customer_filter_for_user()

    with layout("HVAC Dashboard", show_logout=True, show_back=True, back_to="/"):
        render_dashboard(customer_filter)
