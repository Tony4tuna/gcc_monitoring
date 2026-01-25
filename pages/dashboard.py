# pages/dashboard.py
from __future__ import annotations

from nicegui import ui
from typing import Optional, Any

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
            LIMIT 50
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
    tickets = get_open_tickets(customer_id)

    with ui.element("div").classes("gcc-dashboard-grid-item"):
        ui.label("Open Service Tickets").classes("text-lg font-bold mb-2")
        ui.label("Click any row to view ticket details").classes("text-xs gcc-muted mb-2")

        if not tickets:
            ui.label("No open tickets").classes("gcc-muted")
            return

        rows: list[dict] = []
        for t in tickets:
            created_by = "CLIENT" if t.get("hierarchy") == 4 else "TECH/ADMIN"
            short_date = (t.get("created") or "")[:10] if t.get("created") else "—"
            raw_title = (t.get("title") or "").strip()
            issue_only = raw_title.split(" - ")[-1] if " - " in raw_title else raw_title

            rows.append({
                "ticket": t.get("ticket_no") or f"#{t.get('ID')}",
                "created": short_date,
                "customer": (t.get("customer") or "")[:20],
                "location": (t.get("location") or "")[:18],
                "title": issue_only[:40],
                "by": created_by,
                "ticket_id": t.get("ID"),
            })

        columns = [
            {"name": "ticket", "label": "Ticket", "field": "ticket", "align": "right"},
            {"name": "created", "label": "Date", "field": "created", "align": "right"},
            {"name": "customer", "label": "Customer", "field": "customer", "align": "right"},
            {"name": "location", "label": "Location", "field": "location", "align": "right"},
            {"name": "title", "label": "Issue", "field": "title", "align": "right"},
            {"name": "by", "label": "Created By", "field": "by", "align": "right"},
        ]

        table = ui.table(columns=columns, rows=rows, row_key="ticket_id") \
            .classes("gcc-dashboard-table") \
            .props('dense flat virtual-scroll header-align="right"')

        table.add_slot("body-cell-ticket", r"""
          <q-td :props="props">
            <span v-if="props.value && props.value.includes('-')">
              {{ props.value.split('-')[0] }}-<span style="color: #fbbf24;">{{ props.value.split('-')[1] }}</span>
            </span>
            <span v-else>{{ props.value }}</span>
          </q-td>
        """)

        table.add_slot("body-cell-by", r"""
          <q-td :props="props">
            <q-badge :color="props.value === 'CLIENT' ? 'amber' : 'blue'">
              {{ props.value }}
            </q-badge>
          </q-td>
        """)

        def on_ticket_row_click(e) -> None:
            row = _extract_row_from_event_args(e.args)
            if not row:
                return
            ticket_id = _safe_int(row.get("ticket_id"))
            if ticket_id is None:
                return
            ui.navigate.to(f"/tickets?id={ticket_id}")

        # Use rowClick (camelCase) here too
        table.on("rowClick", on_ticket_row_click)


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
# PAGE
# =========================================================

def page():
    if not require_login():
        return

    log_user_action("Viewed Dashboard")
    customer_filter = _get_customer_filter_for_user()

    with layout("Dashboard", show_logout=True, show_back=False, back_to="/"):
        render_dashboard(customer_filter)
