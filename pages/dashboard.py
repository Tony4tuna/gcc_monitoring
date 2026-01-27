# pages/dashboard.py
from __future__ import annotations

from nicegui import ui
from typing import Optional, Any, List, Dict, Tuple

from core.auth import require_login, current_user
from core.db import get_conn
from core.equipment_analysis import calculate_equipment_health_score
from core.alert_system import evaluate_all_alerts
from core.stats import get_summary_counts
from core.version import get_version, get_build_info
from core.setpoints_repo import get_unit_setpoint, create_or_update_setpoint
from ui.layout import layout
from ui.unit_issue_dialog import open_unit_issue_dialog
from core.logger import log_user_action, with_error_handling


# =========================================================
# Helpers
# =========================================================

def _get_customer_filter_for_user() -> Optional[int]:
    """Clients (hierarchy=4) only see their customer_id. Others see all."""
    user = current_user() or {}
    if int(user.get("hierarchy", 5)) == 4:
        return user.get("customer_id")
    return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _extract_row_from_event_args(args: Any) -> Optional[dict]:
    """
    NiceGUI table events often pass:
      [mouseEvent, rowDict, rowIndex]
    Sometimes it passes:
      {"row": {...}, ...}
    """
    if isinstance(args, list):
        if len(args) >= 2 and isinstance(args[1], dict):
            return args[1]
        for item in args:
            if isinstance(item, dict) and "unit_id" in item:
                return item
        return None

    if isinstance(args, dict):
        if "row" in args and isinstance(args["row"], dict):
            return args["row"]
        return args

    return None


def _now():
    from datetime import datetime
    return datetime.now()


def _trim(s: str, max_len: int = 80) -> str:
    s = (s or "").strip()
    return s if len(s) <= max_len else (s[: max_len - 1].rstrip() + "…")


def _build_location_text(data: dict) -> str:
    parts: List[str] = []
    if data.get("location"):
        parts.append(str(data.get("location")))
    city = (data.get("location_city") or "").strip()
    state = (data.get("location_state") or "").strip()
    zip_code = (data.get("location_zip") or "").strip()
    city_state = ", ".join([p for p in [city, state] if p])
    if city_state:
        if zip_code:
            city_state = f"{city_state} {zip_code}"
        parts.append(city_state)
    return ", ".join([p for p in parts if p]).strip() or "—"


def _compose_autodesc(data: dict, alerts: dict) -> str:
    supply = data.get("supply_temp") or "—"
    ret = data.get("return_temp") or "—"
    delta_t = data.get("delta_t") or "—"
    discharge = data.get("discharge_psi") or "—"
    suction = data.get("suction_psi") or "—"
    superheat = data.get("superheat") or "—"
    subcool = data.get("subcooling") or "—"
    amps = data.get("compressor_amps") or "—"
    v1 = data.get("v_1") or "—"
    v2 = data.get("v_2") or "—"
    v3 = data.get("v_3") or "—"
    primary_issue = data.get("fault_code") or "None"

    lines: List[str] = [
        f"Primary Issue: {primary_issue}",
        "Snapshot:",
        f"Supply: {supply} F   Return: {ret} F   ∆T: {delta_t} F",
        f"Discharge: {discharge} PSI   Suction: {suction} PSI",
        f"Superheat: {superheat} F   Subcool: {subcool} F",
        f"Amps: {amps} A   V1/V2/V3: {v1}/{v2}/{v3}",
        "",
        "Top Alerts:",
    ]

    all_alerts = alerts.get("all") or []
    if not all_alerts:
        lines.append("—")
    else:
        for alert in all_alerts[:6]:
            severity = str(alert.get("severity") or "warning").upper()
            code = _trim(str(alert.get("code") or "—"), 24)
            msg = _trim(str(alert.get("message") or "—"), 70)
            lines.append(f"[{severity}] {code}: {msg}")

    return "\n".join(lines)


def _require_reportlab() -> None:
    try:
        import reportlab  # noqa: F401
    except Exception as exc:  # pragma: no cover - runtime guard
        raise RuntimeError(f"ReportLab not installed. Run: pip install reportlab (error: {exc})")


# =========================================================
# DATA
# =========================================================

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
        params: list[Any] = []

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

        units: list[dict] = []
        health_data: dict[int, dict[str, Any]] = {}
        alerts_count = 0

        for r in rows:
            row = dict(r)
            health = calculate_equipment_health_score(row)
            alerts = evaluate_all_alerts(row)

            uid = int(row["unit_id"])
            health_data[uid] = {
                "score": int(health.get("score", 0)),
                "status": health.get("status", "Unknown"),
            }
            alerts_count += int(alerts.get("count", 0))
            units.append(row)

        return {"units": units, "health_data": health_data, "alerts_count": alerts_count}
    finally:
        conn.close()


@with_error_handling("loading tickets status")
def get_tickets_status(customer_id: Optional[int] = None) -> dict:
    """Map unit_id -> newest open ticket info"""
    conn = get_conn()
    try:
        where_parts = ["sc.status IN ('Open', 'OPEN', 'Pending', 'In Progress')"]
        params: list[Any] = []

        if customer_id:
            where_parts.append("sc.customer_id = ?")
            params.append(int(customer_id))

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
            tuple(params),
        ).fetchall()

        tickets_by_unit: dict[int, dict[str, Any]] = {}
        for row in rows:
            r = dict(row)
            uid = _safe_int(r.get("unit_id"))
            if uid is None:
                continue
            if uid not in tickets_by_unit:
                hierarchy = r.get("hierarchy")
                tickets_by_unit[uid] = {
                    "ticket_id": r.get("ticket_id"),
                    "ticket_no": r.get("ticket_no"),
                    "status": r.get("status"),
                    "created": r.get("created"),
                    "is_client": (hierarchy == 4) if hierarchy is not None else False,
                }

        return tickets_by_unit
    finally:
        conn.close()


@with_error_handling("loading open tickets")
def get_open_tickets(customer_id: Optional[int] = None) -> list[dict]:
    """Rows for Open Tickets grid"""
    conn = get_conn()
    try:
        where_parts = ["sc.status IN ('Open', 'OPEN', 'Pending', 'In Progress')"]
        params: list[Any] = []

        if customer_id:
            where_parts.append("sc.customer_id = ?")
            params.append(int(customer_id))

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
            """,
            tuple(params),
        ).fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()


# =========================================================
# TOP CARDS
# =========================================================

def render_top_cards(stats: dict) -> None:
    summary = get_summary_counts()

    with ui.grid(columns=4).classes("gap-3 w-full"):

        def card(title: str, value: Any) -> None:
            with ui.card().classes("gcc-card p-4 text-center"):
                ui.label(title).classes("text-xs gcc-muted")
                ui.label(str(value)).classes("text-2xl font-bold")
                if title == "Equipment":
                    ui.button(
                        "Thermostat",
                        on_click=lambda: ui.navigate.to("/thermostat")
                    ).props("dense outline color=primary").classes("mt-2")

        card("Clients", summary.get("clients", 0))
        card("Locations", summary.get("locations", 0))
        card("Equipment", summary.get("equipment", 0))
        card("Alerts", stats.get("alerts_count", 0))


# =========================================================
# THERMOSTAT DIALOG (reusable)
# =========================================================

_thermostat_dialog: Optional[ui.dialog] = None
_thermostat_controls: dict[str, Any] = {}
_current_unit_id: Optional[int] = None


def _ensure_thermostat_dialog_created() -> None:
    """Create once per page load. Store controls so we can update values later."""
    global _thermostat_dialog, _thermostat_controls

    if _thermostat_dialog is not None:
        return

    user = current_user() or {}

    with ui.dialog() as dlg, ui.card().classes("gcc-card p-4 w-full max-w-2xl"):
        title = ui.label("Thermostat Control").classes("text-lg font-bold mb-3")

        with ui.tabs().classes("w-full") as tabs:
            ui.tab("Settings")
            ui.tab("Schedule")

        with ui.tab_panels(tabs, value="Settings").classes("w-full"):

            # ---------------- SETTINGS TAB ----------------
            with ui.tab_panel("Settings"):
                ui.label("Mode").classes("text-sm font-semibold mb-1")
                mode_select = ui.select(
                    {"Off": "Off", "Cooling": "Cooling", "Heating": "Heating", "Auto": "Auto"},
                    value="Cooling",
                    label="Operating Mode",
                ).classes("w-full mb-4").props("outlined dense")

                ui.label("Temperature Setpoints").classes("text-sm font-semibold mb-2")
                with ui.row().classes("w-full gap-4"):
                    cooling = ui.number(value=72.0, label="Cooling (°F)", min=60, max=85).classes("flex-1").props("outlined dense")
                    heating = ui.number(value=68.0, label="Heating (°F)", min=55, max=80).classes("flex-1").props("outlined dense")

                deadband = ui.number(value=2.0, label="Deadband (°F)", min=0.5, max=5.0).classes("flex-1").props("outlined dense")

                ui.separator().classes("my-2")

                with ui.row().classes("gap-2 justify-end"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")

                    def save_settings() -> None:
                        if _current_unit_id is None:
                            ui.notify("No unit selected", type="negative")
                            return
                        _save_setpoint(
                            unit_id=_current_unit_id,
                            mode=str(mode_select.value),
                            cooling=float(cooling.value),
                            heating=float(heating.value),
                            deadband=float(deadband.value),
                            user_id=user.get("id"),
                            dlg=dlg,
                        )

                    ui.button("Save Settings", on_click=save_settings).props("color=primary")

            # ---------------- SCHEDULE TAB ----------------
            with ui.tab_panel("Schedule"):
                sched_enabled = ui.checkbox("Enable Daily Schedule").classes("mb-3")

                ui.label("Schedule Settings").classes("text-sm font-semibold mb-2")
                with ui.row().classes("w-full gap-4"):
                    sched_day = ui.select(
                        {
                            "Monday": "Monday",
                            "Tuesday": "Tuesday",
                            "Wednesday": "Wednesday",
                            "Thursday": "Thursday",
                            "Friday": "Friday",
                            "Saturday": "Saturday",
                            "Sunday": "Sunday",
                        },
                        value="Monday",
                        label="Day",
                    ).classes("w-32").props("outlined dense")

                    sched_start = ui.input(label="Start Time", value="09:00", placeholder="HH:MM").classes("flex-1").props("outlined dense")
                    sched_end = ui.input(label="End Time", value="17:00", placeholder="HH:MM").classes("flex-1").props("outlined dense")

                ui.label("During Schedule").classes("text-sm font-semibold mb-2")
                with ui.row().classes("w-full gap-4"):
                    sched_mode = ui.select(
                        {"Cooling": "Cooling", "Heating": "Heating", "Auto": "Auto"},
                        value="Cooling",
                        label="Mode",
                    ).classes("w-32").props("outlined dense")

                    sched_temp = ui.number(value=72.0, label="Temperature (°F)", min=60, max=85).classes("flex-1").props("outlined dense")

                ui.separator().classes("my-2")

                with ui.row().classes("gap-2 justify-end"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")

                    def save_schedule() -> None:
                        if _current_unit_id is None:
                            ui.notify("No unit selected", type="negative")
                            return
                        _save_schedule(
                            unit_id=_current_unit_id,
                            enabled=bool(sched_enabled.value),
                            day=str(sched_day.value),
                            start=str(sched_start.value),
                            end=str(sched_end.value),
                            mode=str(sched_mode.value),
                            temp=float(sched_temp.value),
                            user_id=user.get("id"),
                            dlg=dlg,
                        )

                    ui.button("Save Schedule", on_click=save_schedule).props("color=primary")

    _thermostat_dialog = dlg
    _thermostat_controls = {
        "title": title,
        "mode": mode_select,
        "cooling": cooling,
        "heating": heating,
        "deadband": deadband,
        "sched_enabled": sched_enabled,
        "sched_day": sched_day,
        "sched_start": sched_start,
        "sched_end": sched_end,
        "sched_mode": sched_mode,
        "sched_temp": sched_temp,
    }


def show_thermostat_dialog(unit_id: int) -> None:
    """Load setpoint data into controls and open dialog."""
    global _current_unit_id

    _ensure_thermostat_dialog_created()
    if _thermostat_dialog is None:
        ui.notify("Dialog not initialized", type="negative")
        return

    unit_id_int = _safe_int(unit_id)
    if unit_id_int is None:
        ui.notify("Invalid unit id", type="negative")
        return

    _current_unit_id = unit_id_int
    sp = get_unit_setpoint(unit_id_int) or {}

    # set values into UI fields
    _thermostat_controls["mode"].set_value(sp.get("mode", "Cooling"))
    _thermostat_controls["cooling"].set_value(sp.get("cooling_setpoint", 72.0))
    _thermostat_controls["heating"].set_value(sp.get("heating_setpoint", 68.0))
    _thermostat_controls["deadband"].set_value(sp.get("deadband", 2.0))

    _thermostat_controls["sched_enabled"].set_value(bool(sp.get("schedule_enabled", 0)))
    _thermostat_controls["sched_day"].set_value(sp.get("schedule_day", "Monday"))
    _thermostat_controls["sched_start"].set_value(sp.get("schedule_start_time", "09:00"))
    _thermostat_controls["sched_end"].set_value(sp.get("schedule_end_time", "17:00"))
    _thermostat_controls["sched_mode"].set_value(sp.get("schedule_mode", "Cooling"))
    _thermostat_controls["sched_temp"].set_value(sp.get("schedule_temp", 72.0))

    _thermostat_dialog.open()


def _save_setpoint(unit_id: int, mode: str, cooling: float, heating: float, deadband: float,
                   user_id: Optional[int], dlg) -> None:
    try:
        create_or_update_setpoint(
            unit_id=unit_id,
            mode=mode,
            cooling_setpoint=cooling,
            heating_setpoint=heating,
            deadband=deadband,
            updated_by_login_id=user_id,
        )
        ui.notify("Setpoint saved", type="positive")
        dlg.close()
    except Exception as e:
        ui.notify(f"Error saving setpoint: {e}", type="negative")


def _save_schedule(unit_id: int, enabled: bool, day: str, start: str, end: str,
                   mode: str, temp: float, user_id: Optional[int], dlg) -> None:
    try:
        # very simple time validation
        for t in [start, end]:
            parts = str(t).split(":")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                ui.notify("Invalid time format. Use HH:MM", type="negative")
                return

        # keep base settings (your repo function can decide what to do)
        create_or_update_setpoint(
            unit_id=unit_id,
            mode="Auto",
            cooling_setpoint=72.0,
            heating_setpoint=68.0,
            deadband=2.0,
            schedule_enabled=1 if enabled else 0,
            schedule_day=day,
            schedule_start_time=start,
            schedule_end_time=end,
            schedule_mode=mode,
            schedule_temp=temp,
            updated_by_login_id=user_id,
        )
        ui.notify("Schedule saved", type="positive")
        dlg.close()
    except Exception as e:
        ui.notify(f"Error saving schedule: {e}", type="negative")


# =========================================================
# ADMIN: UNITS GRID (ROW CLICK + ICON CLICK)
# =========================================================

def render_admin_units_grid(stats: dict, tickets_by_unit: dict) -> None:
    with ui.element("div").classes("gcc-dashboard-grid-item"):
        ui.label("Units With Warnings / Alarms").classes("text-lg font-bold mb-2")
        ui.label("Click row = Unit details • Click gear = Thermostat").classes("text-xs gcc-muted mb-2")

        # build table rows (only warning/alarm units)
        rows: list[dict] = []
        for u in stats.get("units", []):
            uid = _safe_int(u.get("unit_id"))
            if uid is None:
                continue

            score = int(stats.get("health_data", {}).get(uid, {}).get("score", 0))
            if score >= 80:
                continue

            rows.append({
                "client": str(u.get("customer_id") or u.get("customer") or ""),
                "location": (u.get("location") or "")[:30],
                "unit": f"RTU-{uid}",
                "temp": f"{u.get('supply_temp')}°F" if u.get("supply_temp") is not None else "—",
                "mode": u.get("mode") or "—",
                "fault": u.get("fault_code") or "—",
                "unit_id": uid,
            })

        if not rows:
            ui.label("No warnings or alarms right now.").classes("gcc-muted")
            return

        columns = [
            {"name": "client", "label": "Client", "field": "client", "align": "right"},
            {"name": "location", "label": "Location", "field": "location", "align": "right"},
            {"name": "unit", "label": "Tag", "field": "unit", "align": "right"},
            {"name": "temp", "label": "Temp", "field": "temp", "align": "right"},
            {"name": "mode", "label": "Mode", "field": "mode", "align": "right"},
            {"name": "fault", "label": "Fault", "field": "fault", "align": "right"},
        ]

        table = ui.table(columns=columns, rows=rows, row_key="unit_id") \
            .classes("gcc-dashboard-table") \
            .props('dense flat virtual-scroll header-align="right"')

                # (Thermostat icon removed; use dedicated Thermostat page instead)

        def on_row_click(e) -> None:
            row = _extract_row_from_event_args(e.args)
            if not row:
                ui.notify("Row click: no row data", type="negative")
                return

            unit_id = _safe_int(row.get("unit_id"))
            if unit_id is None:
                ui.notify("Row click: unit_id missing", type="negative")
                return

            open_unit_issue_dialog(unit_id)

        # Use rowClick (camelCase) for table row click
        table.on("rowClick", on_row_click)
        


# =========================================================
# OPEN TICKETS GRID
# =========================================================

def render_tickets_grid(customer_id: Optional[int]) -> None:
    from core.tickets_repo import list_service_calls, search_service_calls
    
    with ui.element("div").classes("gcc-dashboard-grid-item"):
        ui.label("Service Tickets").classes("text-lg font-bold mb-2")
        
        # Filters
        with ui.row().classes("gap-3 items-center flex-wrap mb-2"):
            search_input = ui.input("Search").classes("w-60")
            status_filter = ui.select(["All", "Open", "In Progress", "Closed"], value="All", label="Status").classes("w-32")
            priority_filter = ui.select(["All", "Low", "Normal", "High", "Emergency"], value="All", label="Priority").classes("w-32")
        
        # Action buttons
        with ui.row().classes("gap-2 mb-2"):
            new_btn = ui.button(icon="add_circle", on_click=lambda: open_ticket_dialog("new")).props("flat dense color=positive")
            view_btn = ui.button(icon="visibility", on_click=lambda: open_ticket_dialog("view")).props("flat dense")
            edit_btn = ui.button(icon="edit", on_click=lambda: open_ticket_dialog("edit")).props("flat dense")
            close_btn = ui.button(icon="check_circle", on_click=lambda: open_ticket_dialog("close")).props("flat dense color=green")
            delete_btn = ui.button(icon="delete", on_click=lambda: open_ticket_dialog("delete")).props("flat dense color=negative")
            print_btn = ui.button(icon="print", on_click=lambda: open_ticket_dialog("print")).props("flat dense")
            refresh_btn = ui.button(icon="refresh", on_click=lambda: refresh_tickets()).props("flat dense")

        columns = [
            {"name": "ID", "label": "ID", "field": "ID", "align": "left"},
            {"name": "title", "label": "Title", "field": "title", "align": "left"},
            {"name": "customer", "label": "Customer", "field": "customer", "align": "left"},
            {"name": "location", "label": "Location", "field": "location", "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "align": "center"},
            {"name": "priority", "label": "Priority", "field": "priority", "align": "center"},
            {"name": "created", "label": "Created", "field": "created", "align": "left"},
        ]

        table = ui.table(columns=columns, rows=[], row_key="ID", selection="single") \
            .classes("gcc-dashboard-table") \
            .props('dense flat virtual-scroll header-align="left"')
        
        def update_button_states():
            has_selection = bool(table.selected)
            if has_selection:
                view_btn.enable()
                edit_btn.enable()
                selected = table.selected[0]
                if selected.get("status") != "Closed":
                    close_btn.enable()
                    delete_btn.disable()
                else:
                    close_btn.disable()
                    delete_btn.enable()
                print_btn.enable()
            else:
                view_btn.disable()
                edit_btn.disable()
                close_btn.disable()
                delete_btn.disable()
                print_btn.disable()

        def refresh_tickets():
            search_term = search_input.value
            status = None if status_filter.value == "All" else status_filter.value
            priority = None if priority_filter.value == "All" else priority_filter.value

            if search_term:
                calls = search_service_calls(search_term, customer_id)
            else:
                calls = list_service_calls(customer_id=customer_id, status=status, priority=priority)

            rows = []
            for call in calls:
                customer_name = call.get("customer_name")
                if not customer_name and call.get("customer_id"):
                    customer_name = f"Customer #{call.get('customer_id')}"

                rows.append({
                    "ID": call.get("ID"),
                    "title": (call.get("title") or "Untitled")[:60],
                    "customer": (customer_name or "—")[:40],
                    "location": (call.get("location_address") or "—")[:60],
                    "status": call.get("status", "—"),
                    "priority": call.get("priority", "—"),
                    "created": (call.get("created") or "")[:16],
                    "_full_data": call,
                })

            table.rows = rows
            table.update()
            update_button_states()

        def open_ticket_dialog(mode: str):
            from pages.tickets import show_ticket_detail, show_edit_dialog, show_close_dialog, confirm_delete, show_print_call, render_call_form
            
            if mode == "new":
                render_call_form(customer_id, current_user() or {}, current_user().get("hierarchy", 5))
                return

            if not table.selected:
                ui.notify("Select a service call first", type="warning")
                return

            selected = table.selected[0]
            full_data = selected.get("_full_data", selected)
            call_id = selected["ID"]

            if mode == "view":
                show_ticket_detail(full_data)
            elif mode == "edit":
                show_edit_dialog(full_data)
            elif mode == "close":
                show_close_dialog(call_id)
            elif mode == "delete":
                confirm_delete(call_id)
            elif mode == "print":
                show_print_call(full_data)

        table.on("update:selected", lambda: update_button_states())
        search_input.on("keydown.enter", lambda: refresh_tickets())
        status_filter.on_value_change(lambda: refresh_tickets())
        priority_filter.on_value_change(lambda: refresh_tickets())

        update_button_states()
        refresh_tickets()


# =========================================================
# DASHBOARD
# =========================================================

def render_dashboard(customer_id: Optional[int]) -> None:
    user = current_user() or {}
    admin = int(user.get("hierarchy", 5)) != 4

    # Create dialog ONCE so it exists for the icon event
    _ensure_thermostat_dialog_created()

    ui.add_head_html("""
    <style>
      .gcc-dashboard-table thead th {
        background: rgba(255, 255, 255, 0.06);
        font-weight: 700;
        color: #e5e7eb;
      }
    </style>
    """)

    stats = get_unit_stats(customer_id if not admin else None)
    tickets_by_unit = get_tickets_status(customer_id if not admin else None)

    render_top_cards(stats)

    if admin:
        with ui.element("div").classes("gcc-dashboard-grid"):
            render_admin_units_grid(stats, tickets_by_unit)
            render_tickets_grid(customer_id if not admin else None)
    else:
        ui.label("Client dashboard unchanged").classes("gcc-muted")

    with ui.row().classes("text-xs gcc-muted mt-6 justify-center"):
        ui.label(f"GCC Monitoring v{get_version()} • Built {get_build_info().get('build_date','—')}")


# =========================================================
# PDF GENERATION
# =========================================================

def _generate_ticket_no(call_id: int) -> str:
    from datetime import datetime

    date_part = datetime.now().strftime("%Y%m%d")
    num_part = f"{call_id:04d}"
    return f"{date_part}-{num_part}"


def generate_service_order_pdf(ticket_no: str, data: dict, health: dict, alerts: dict, company: dict) -> Tuple[str, bytes]:
    """Generate service order PDF matching the legacy canvas-based layout."""
    _require_reportlab()

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import os

    os.makedirs("reports/service_orders", exist_ok=True)

    unit_id = int(data.get("unit_id") or 0)
    unit_name = f"RTU-{unit_id}" if unit_id else "UNIT"
    filename = f"ServiceOrder_{ticket_no}_{unit_name}.pdf"
    pdf_path = os.path.join("reports", "service_orders", filename)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    left = 40
    right = width - 40
    y = height - 40

    def text(x: float, y_pos: float, s: str, size: int = 10, bold: bool = False) -> None:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y_pos, s)

    # Header
    comp_name = company.get("company") or company.get("name") or "GCC Technology"
    text(left, y, comp_name, 14, True)
    y -= 16
    for line in [
        company.get("address1") or "",
        company.get("address2") or "",
        " ".join([
            p
            for p in [
                (company.get("city") or "").strip(),
                (company.get("state") or "").strip(),
                (company.get("zip") or "").strip(),
            ]
            if p
        ]).strip(),
    ]:
        if line.strip():
            text(left, y, line.strip(), 10)
            y -= 12

    contact_line = " | ".join(
        [
            p
            for p in [
                (company.get("phone") or "").strip(),
                (company.get("email") or "").strip(),
                (company.get("website") or "").strip(),
            ]
            if p
        ]
    ).strip()
    if contact_line:
        text(left, y, contact_line, 9)
        y -= 14

    c.line(left, y, right, y)
    y -= 18

    # Title on the left; ticket/date/time column on the right, matching requested spacing
    text(left, y, "HVAC Service Order Invoice", 12, True)
    now = _now()
    info_x = right - 210
    text(info_x, y, f"Ticket #: {ticket_no}", 9)
    y -= 12
    text(info_x, y, f"Date    : {now.strftime('%m/%d/%Y')}", 9)
    y -= 12
    text(info_x, y, f"Time    : {now.strftime('%H:%M:%S')}", 9)
    y -= 8
    c.line(left, y, right, y)
    y -= 18

    mid = (left + right) / 2

    lx = left
    ly = y
    text(lx, ly, "CONTACT INFORMATION", 10, True)
    ly -= 12
    text(lx, ly, f"Customer: {data.get('customer', '—')}", 9)
    ly -= 11
    text(lx, ly, f"Location: {_build_location_text(data)}", 9)
    ly -= 11
    text(lx, ly, f"Phone: {data.get('customer_phone') or '—'}", 9)
    ly -= 11
    text(lx, ly, f"Email: {data.get('customer_email') or '—'}", 9)
    ly -= 14

    text(lx, ly, "UNIT INFORMATION", 10, True)
    ly -= 12
    text(lx, ly, f"Unit: RTU-{unit_id}", 9)
    ly -= 11
    text(lx, ly, f"Make/Model: {data.get('make', '—')} {data.get('model', '—')}", 9)
    ly -= 11
    text(lx, ly, f"Serial #: {data.get('serial', '—')}", 9)
    ly -= 11
    score = int(health.get("score", 0) or 0)
    text(lx, ly, f"Mode: {data.get('mode', '—')}   Health: {score}% ({health.get('status', 'Unknown')})", 9)
    ly -= 11
    text(lx, ly, f"Fault Code: {data.get('fault_code') or 'None'}", 9)
    ly -= 14

    rx = mid + 18
    ry = y
    text(rx, ry, "DESCRIPTION (AUTO)", 10, True)
    ry -= 12
    c.setFont("Helvetica", 8.7)
    for line in _compose_autodesc(data, alerts).splitlines()[:20]:
        c.drawString(rx, ry, line)
        ry -= 10

    c.line(mid, y + 10, mid, min(ly, ry) - 20)

    y2 = min(ly, ry) - 25
    c.line(left, y2, right, y2)
    y2 -= 14

    def _wrap_text(content: str, max_width: float, font: str = "Helvetica", size: int = 9) -> List[str]:
        """Simple word-wrap that respects the current font metrics."""
        c.setFont(font, size)
        words = (content or "").split()
        lines: List[str] = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if c.stringWidth(candidate, font, size) <= max_width:
                line = candidate
            else:
                lines.append(line or word)
                line = word
        if line:
            lines.append(line)
        return lines or [""]

    def _draw_boxed_section(title: str, content: str, y_start: float) -> float:
        box_height = 128
        text(left, y_start, title, 10, True)
        y_start -= 12
        c.rect(left, y_start - box_height, right - left, box_height, stroke=1, fill=0)

        # Render text inside the box with padding and wrapping
        usable_width = (right - left) - 12
        line_y = y_start - 14
        line_height = 11
        max_lines = int((box_height - 12) / line_height)
        wrapped = _wrap_text(content or "—", usable_width)
        for line in wrapped[:max_lines]:
            c.drawString(left + 6, line_y, line)
            line_y -= line_height

        return y_start - box_height - 12

    y2 -= 8  # blank line before materials box
    y2 = _draw_boxed_section("MATERIALS & SERVICES (TECH TO FILL)", data.get("materials_services") or "", y2)
    y2 -= 8  # blank line before labor box
    y2 = _draw_boxed_section("LABOR DESCRIPTION (TECH TO FILL)", data.get("labor_description") or "", y2)

    y2 -= 48  # space between last box and signature (3 extra lines)
    text(left, y2, "Customer Signature: ____________________________   Date: ____________", 9)

    c.showPage()
    c.save()

    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    if not pdf_bytes or len(pdf_bytes) < 500:
        raise RuntimeError(f"PDF generation failed (too small): {pdf_path} ({len(pdf_bytes)} bytes)")

    return pdf_path, pdf_bytes


# PAGE
# =========================================================

def page():
    if not require_login():
        return

    log_user_action("Viewed Dashboard")
    customer_filter = _get_customer_filter_for_user()

    with layout("Dashboard", show_logout=True, show_back=False, back_to="/"):
        render_dashboard(customer_filter)
